"""
LLM 生成器

提供各种生成器用于创建术语表、DAG、模块设计等。
使用 Azure OpenAI Structured Outputs 功能，简化 JSON 解析逻辑。
"""
import time
from typing import Optional

import networkx as nx
from pydantic import BaseModel

from docuflow.core.models import (
    AppConfig, ArchitectureDAG, Glossary, GlossaryEntry, LLMContext,
    ModuleSummaryResponse, CritiqueResult,
)
from docuflow.llm.client import AzureOpenAIClient
from docuflow.llm.prompts import (
    MAX_DOCUMENT_SIZE, MAX_MODULE_SIZE,
    MARKDOWN_SYSTEM_PROMPT,
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
        self.client = AzureOpenAIClient(
            temperature=config.llm_temperature,
            timeout=config.llm_timeout,
            max_retries=config.llm_max_retries_sdk,
            max_concurrent=config.llm_max_concurrent,
        )
        self.logger = get_logger()

    def _unwrap_single_code_fence(self, text: str) -> str:
        """Unwrap a single outer ```markdown fence when the model wraps the whole answer."""
        import re

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
        min_length: int = 0,
        error_msg: str = "生成内容过短",
        system_prompt: Optional[str] = None,
    ):
        """通用生成方法（文本输出）"""
        system_prompt = system_prompt or MARKDOWN_SYSTEM_PROMPT

        def _generate():
            response = self.client.generate(prompt, system_prompt=system_prompt)
            response = self._unwrap_single_code_fence(response or "")

            if min_length > 0 and (not response or len(response.strip()) < min_length):
                raise LLMGenerationError(error_msg, retryable=True)
            return response

        return self._retry_with_backoff(_generate)


class GlossaryGenerator(BaseGenerator):
    """术语表生成器（使用结构化输出）"""

    # 术语表响应模型
    class GlossaryResponse(BaseModel):
        """术语表响应（用于结构化输出）"""
        entries: list[GlossaryEntry] = []

    def generate(self, document_content: str) -> Glossary:
        self.logger.info("正在生成术语表...")
        prompt = GLOSSARY_PROMPT.format(document_content=document_content[:MAX_DOCUMENT_SIZE])

        def _generate():
            response = self.client.generate_structured(
                prompt,
                response_model=self.GlossaryResponse,
            )
            return Glossary(entries=response.entries)

        return self._retry_with_backoff(_generate)


class DAGGenerator(BaseGenerator):
    """架构 DAG 生成器（使用结构化输出）"""

    def generate(self, document_content: str, glossary_content: str) -> ArchitectureDAG:
        self.logger.info("正在生成架构 DAG...")

        def _generate():
            prompt = DAG_PROMPT.format(
                glossary=glossary_content,
                document_content=document_content[:MAX_DOCUMENT_SIZE]
            )
            dag = self.client.generate_structured(
                prompt,
                response_model=ArchitectureDAG,
            )
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
    """模块摘要生成器（使用结构化输出）"""

    def generate(self, module_name: str, module_content: str) -> dict:
        self.logger.info(f"正在提取模块摘要: {module_name}")
        prompt = MODULE_SUMMARY_PROMPT.format(
            module_name=module_name,
            module_content=module_content[:MAX_MODULE_SIZE],
        )

        def _generate():
            response = self.client.generate_structured(
                prompt,
                response_model=ModuleSummaryResponse,
            )
            return response.model_dump()

        return self._retry_with_backoff(_generate)


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
    """模块设计批判生成器（使用结构化输出）"""

    def __init__(self, config: AppConfig):
        super().__init__(config)
        # 如果配置了批判专用模型，使用该模型
        if config.critique_model:
            self.client = AzureOpenAIClient(
                temperature=config.llm_temperature,
                model_name=config.critique_model,
                timeout=config.llm_timeout,
                max_retries=config.llm_max_retries_sdk,
                max_concurrent=config.llm_max_concurrent,
            )
            self.logger.info(f"批判使用独立模型: {config.critique_model}")

    def critique(self, module_name: str, module_design: str,
                 context: LLMContext, threshold: float) -> dict:
        """
        批判评估模块设计（使用结构化输出）

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

        def _generate():
            result = self.client.generate_structured(
                prompt,
                response_model=CritiqueResult,
            )

            # 强制校验 passed 与 score 的一致性
            score = result.score
            if score >= threshold:
                result.passed = True

            self.logger.info(
                f"模块 '{module_name}' 批判结果: "
                f"{'通过' if result.passed else '未通过'} (分数: {score:.2f})"
            )
            return {
                "passed": result.passed,
                "score": score,
                "issues": result.issues,
                "suggestions": result.suggestions,
            }

        return self._retry_with_backoff(_generate)
