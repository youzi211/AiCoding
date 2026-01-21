"""
LLM 生成器

提供各种生成器用于创建术语表、DAG、模块设计等。
"""
import json
import re
import time
from typing import Optional

import networkx as nx

# 尝试导入 json5 作为备选解析器（更宽松的 JSON 解析）
try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False

from docuflow.core.models import (
    AppConfig, ArchitectureDAG, Glossary, GlossaryEntry, LLMContext
)
from docuflow.llm.client import AzureOpenAIClient
from docuflow.llm.prompts import (
    MAX_DOCUMENT_SIZE, MAX_MODULE_SIZE,
    JSON_SYSTEM_PROMPT, MARKDOWN_SYSTEM_PROMPT,
    GLOSSARY_PROMPT, DAG_PROMPT, MODULE_DESIGN_PROMPT,
    MODULE_SUMMARY_PROMPT, SYSTEM_DESIGN_PROMPT,
    INTERFACE_PROMPT, DATABASE_PROMPT,
    CRITIQUE_PROMPT, REGENERATE_PROMPT
)
from docuflow.utils import get_logger


class LLMGenerationError(Exception):
    """LLM 生成失败的异常"""

    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class BaseGenerator:
    """生成器基类"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.client = AzureOpenAIClient(temperature=config.llm_temperature)
        self.logger = get_logger()

    def _extract_json(self, response: str) -> dict:
        """从响应中提取 JSON，支持多种容错处理"""
        normalized = self._normalize_output(response)
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", normalized, flags=re.IGNORECASE)
        json_str = (json_match.group(1) if json_match else normalized).strip()

        # Best-effort: if there's leading/trailing prose, keep the first JSON object.
        # 使用更智能的正则来找到完整的 JSON 对象
        if not json_str.startswith("{"):
            # 尝试匹配从第一个 { 到最后一个 } 的完整 JSON 对象
            brace_count = 0
            start_idx = -1
            end_idx = -1
            in_string = False
            escape_next = False

            for i, char in enumerate(json_str):
                if escape_next:
                    escape_next = False
                elif char == '\\':
                    escape_next = True
                elif char == '"' and not escape_next:
                    in_string = not in_string
                elif not in_string:
                    if char == '{' and start_idx == -1:
                        start_idx = i
                        brace_count = 1
                    elif char == '{':
                        brace_count += 1
                    elif char == '}' and start_idx != -1:
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break

            if start_idx != -1 and end_idx != -1:
                json_str = json_str[start_idx:end_idx].strip()

        # 验证提取的内容看起来像 JSON
        if not json_str or (not json_str.startswith('{') and not json_str.startswith('[')):
            raise LLMGenerationError(f"响应不包含有效的 JSON 对象。提取的内容: {json_str[:200]}", retryable=True)

        # 尝试多种解析策略
        strategies = [
            ("标准 JSON 解析", lambda s: json.loads(s)),
            ("json5 宽松解析", lambda s: json5.loads(s) if HAS_JSON5 else None),
            ("清理后解析", self._parse_with_cleanup),
        ]

        last_error = None
        for strategy_name, parser in strategies:
            try:
                if parser is None:
                    continue
                result = parser(json_str)
                if result is not None:
                    self.logger.debug(f"使用 {strategy_name} 成功解析 JSON")
                    return result
            except Exception as e:
                last_error = e
                self.logger.debug(f"{strategy_name} 失败: {e}")
                continue

        # 所有策略都失败，记录错误并抛出异常
        self.logger.error(f"JSON 解析失败。原始响应（前500字符）: {response}")
        # self.logger.error(f"提取的 JSON 字符串（前500字符）: {json_str[:500]}")
        raise LLMGenerationError(f"无法解析 JSON: {last_error}", retryable=True) from last_error

    def _parse_with_cleanup(self, json_str: str) -> dict:
        """尝试清理常见的 JSON 格式问题后解析"""
        import re

        # 使用更强大的正则来修复 JSON
        # 主要问题：字符串内部包含未转义的换行符

        # 策略：逐字符处理，修复字符串内的换行
        result = []
        in_string = False
        escape_next = False
        i = 0

        while i < len(json_str):
            char = json_str[i]

            if escape_next:
                # 转义序列的一部分，直接添加
                result.append(char)
                escape_next = False
            elif char == '\\':
                # 转义字符开始
                result.append(char)
                escape_next = True
            elif char == '"':
                # 引号
                result.append(char)
                in_string = not in_string
            elif char in '\n\r':
                # 换行符
                if in_string:
                    # 在字符串内部，转义换行符
                    result.append('\\n' if char == '\n' else '\\r')
                else:
                    # 在字符串外部，保留（虽然是非法的，但可能是格式问题）
                    # 我们选择移除它
                    pass
            else:
                # 其他字符
                result.append(char)

            i += 1

        cleaned = ''.join(result)

        # 移除尾随逗号
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)

        return json.loads(cleaned)

    def _normalize_output(self, text: str) -> str:
        """Normalize common LLM output issues (quotes/whitespace) to improve parsing/rendering."""
        if not text:
            return ""
        table = str.maketrans({
            "“": '"',
            "”": '"',
            "„": '"',
            "«": '"',
            "»": '"',
            "‘": "'",
            "’": "'",
            "‚": "'",
            "‛": "'",
            "\u00a0": " ",
            "\u200b": "",
            "\ufeff": "",
            "\u200e": "",
            "\u200f": "",
        })
        return text.translate(table)

    def _unwrap_single_code_fence(self, text: str) -> str:
        """Unwrap a single outer ```markdown fence when the model wraps the whole answer."""
        stripped = (text or "").strip()
        match = re.match(r"^```(?:markdown|md)?\s*([\s\S]*?)\s*```$", stripped, flags=re.IGNORECASE)
        if not match:
            return text
        inner = match.group(1).strip()
        # Don't unwrap if there are nested fences inside (e.g. Mermaid code blocks).
        if "```" in inner:
            return text
        return inner

    def _retry_with_backoff(self, func, max_retries: Optional[int] = None):
        """使用指数退避重试"""
        max_retries = max_retries or self.config.max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                return func()
            except LLMGenerationError as e:
                last_error = e
                if not e.retryable:
                    raise
                wait_time = 2 ** attempt
                self.logger.warning(f"尝试 {attempt + 1}/{max_retries} 失败: {e}，{wait_time}秒后重试...")
                time.sleep(wait_time)
            except Exception as e:
                last_error = LLMGenerationError(str(e))
                wait_time = 2 ** attempt
                self.logger.warning(f"尝试 {attempt + 1}/{max_retries} 错误: {e}，{wait_time}秒后重试...")
                time.sleep(wait_time)

        raise last_error or LLMGenerationError("超过最大重试次数")

    def _generate_with_validation(
        self,
        prompt: str,
        parse_json: bool = False,
        min_length: int = 0,
        error_msg: str = "生成内容过短",
        system_prompt: Optional[str] = None,
    ):
        """通用生成方法"""
        system_prompt = system_prompt or (JSON_SYSTEM_PROMPT if parse_json else MARKDOWN_SYSTEM_PROMPT)

        def _generate():
            response = self.client.generate(prompt, system_prompt=system_prompt)
            response = self._normalize_output(response or "")
            if not parse_json:
                response = self._unwrap_single_code_fence(response)

            if min_length > 0 and (not response or len(response.strip()) < min_length):
                raise LLMGenerationError(error_msg, retryable=True)
            return self._extract_json(response) if parse_json else response

        return self._retry_with_backoff(_generate)


class GlossaryGenerator(BaseGenerator):
    """术语表生成器"""

    def generate(self, document_content: str) -> Glossary:
        self.logger.info("正在生成术语表...")
        prompt = GLOSSARY_PROMPT.format(document_content=document_content[:MAX_DOCUMENT_SIZE])
        data = self._generate_with_validation(prompt, parse_json=True)

        entries = [
            GlossaryEntry(
                term=e["term"],
                definition=e["definition"],
                category=e.get("category"),
                aliases=e.get("aliases", [])
            )
            for e in data.get("entries", [])
        ]
        return Glossary(entries=entries)


class DAGGenerator(BaseGenerator):
    """架构 DAG 生成器"""

    def generate(self, document_content: str, glossary_content: str) -> ArchitectureDAG:
        self.logger.info("正在生成架构 DAG...")

        def _generate():
            prompt = DAG_PROMPT.format(
                glossary=glossary_content,
                document_content=document_content[:MAX_DOCUMENT_SIZE]
            )
            response = self.client.generate(prompt)
            data = self._extract_json(response)
            dag = ArchitectureDAG.model_validate(data)
            self._validate_dag(dag)
            return dag

        return self._retry_with_backoff(_generate)

    def _validate_dag(self, dag: ArchitectureDAG) -> None:
        """验证 DAG 无环"""
        G = nx.DiGraph()
        module_names = {m.name for m in dag.modules}

        for module in dag.modules:
            G.add_node(module.name)
            for dep in module.dependencies:
                if dep not in module_names:
                    raise LLMGenerationError(f"模块 '{module.name}' 依赖未知模块 '{dep}'", retryable=True)
                G.add_edge(dep, module.name)

        if not nx.is_directed_acyclic_graph(G):
            cycles = list(nx.simple_cycles(G))
            raise LLMGenerationError(f"图包含循环: {cycles}", retryable=True)


class ModuleDesignGenerator(BaseGenerator):
    """模块设计生成器"""

    def generate(self, module_name: str, context: LLMContext) -> str:
        self.logger.info(f"正在生成模块设计: {module_name}")
        prompt = MODULE_DESIGN_PROMPT.format(
            module_name=module_name,
            context=context.to_context_string()
        )
        return self._generate_with_validation(prompt, min_length=100, error_msg="模块设计内容过短")

    def regenerate(self, module_name: str, current_design: str,
                   critique_result: dict, context: LLMContext,
                   threshold: float = 0.7) -> str:
        """根据批判反馈重新生成模块设计"""
        self.logger.info(f"正在根据反馈改进模块设计: {module_name}")
        issues = critique_result.get("issues", [])
        prompt = REGENERATE_PROMPT.format(
            module_name=module_name,
            current_design=current_design[:MAX_MODULE_SIZE],
            score=critique_result.get("score", 0),
            threshold=threshold,
            issues="\n".join(f"- {i}" for i in issues) if issues else "无",
            suggestions=critique_result.get("suggestions", ""),
            context=context.to_context_string()
        )
        return self._generate_with_validation(prompt, min_length=100, error_msg="改进后的模块设计内容过短")


class ModuleSummaryGenerator(BaseGenerator):
    """模块摘要生成器"""

    def generate(self, module_name: str, module_content: str) -> dict:
        self.logger.info(f"正在提取模块摘要: {module_name}")
        prompt = MODULE_SUMMARY_PROMPT.format(
            module_name=module_name,
            module_content=module_content[:MAX_MODULE_SIZE],
        )
        return self._generate_with_validation(prompt, parse_json=True)


class SystemDesignGenerator(BaseGenerator):
    """系统级设计生成器"""

    def generate_system_design(
        self,
        summaries_text: str,
        *,
        dag_overview: str = "",
        glossary_excerpt: str = "",
        requirements_excerpt: str = "",
    ) -> str:
        self.logger.info("正在生成系统设计...")
        prompt = SYSTEM_DESIGN_PROMPT.format(
            requirements_excerpt=requirements_excerpt,
            glossary_excerpt=glossary_excerpt,
            dag_overview=dag_overview,
            module_summaries=summaries_text,
        )
        return self._generate_with_validation(prompt, min_length=100, error_msg="系统设计内容过短")

    def generate_interface_design(
        self,
        summaries_text: str,
        *,
        dag_overview: str = "",
        glossary_excerpt: str = "",
        requirements_excerpt: str = "",
    ) -> str:
        self.logger.info("正在生成接口设计...")
        prompt = INTERFACE_PROMPT.format(
            requirements_excerpt=requirements_excerpt,
            glossary_excerpt=glossary_excerpt,
            dag_overview=dag_overview,
            module_summaries=summaries_text,
        )
        return self._generate_with_validation(prompt, min_length=100, error_msg="接口设计内容过短")

    def generate_database_design(
        self,
        summaries_text: str,
        *,
        dag_overview: str = "",
        glossary_excerpt: str = "",
        requirements_excerpt: str = "",
    ) -> str:
        self.logger.info("正在生成数据库设计...")
        prompt = DATABASE_PROMPT.format(
            requirements_excerpt=requirements_excerpt,
            glossary_excerpt=glossary_excerpt,
            dag_overview=dag_overview,
            module_summaries=summaries_text,
        )
        return self._generate_with_validation(prompt, min_length=100, error_msg="数据库设计内容过短")


class ModuleCritiqueGenerator(BaseGenerator):
    """模块设计批判生成器"""

    def __init__(self, config: AppConfig):
        super().__init__(config)
        # 如果配置了批判专用模型，使用该模型
        if config.critique_model:
            self.client = AzureOpenAIClient(
                temperature=config.llm_temperature,
                model_name=config.critique_model
            )
            self.logger.info(f"批判使用独立模型: {config.critique_model}")

    def critique(self, module_name: str, module_design: str,
                 context: LLMContext, threshold: float) -> dict:
        """
        批判评估模块设计

        Args:
            module_name: 模块名称
            module_design: 模块设计内容
            context: LLM 上下文
            threshold: 通过阈值

        Returns:
            dict: {"passed": bool, "score": float, "issues": list, "suggestions": str}
        """
        self.logger.info(f"正在批判评估模块设计: {module_name}")
        prompt = CRITIQUE_PROMPT.format(
            module_name=module_name,
            module_design=module_design[:MAX_MODULE_SIZE],
            context=context.to_context_string(),
            threshold=threshold
        )
        result = self._generate_with_validation(prompt, parse_json=True)

        # 强制校验 passed 与 score 的一致性
        score = result.get("score", 0)
        result["passed"] = score >= threshold

        self.logger.info(
            f"模块 '{module_name}' 批判结果: "
            f"{'通过' if result['passed'] else '未通过'} (分数: {score:.2f})"
        )
        return result
