"""LangGraph 节点实现"""
import json
from datetime import datetime
from typing import Any

import networkx as nx

from docuflow.graph.state import DocuFlowState
from docuflow.core.models import (
    AppConfig, ArchitectureDAG, ProjectStatus, ModuleProgress,
    ModuleStatus, LLMContext, ModuleDefinition, CritiqueLogEntry
)
from docuflow.parsers import DocumentParserFactory, DocumentChunker, ChunkRetriever
from docuflow.llm import (
    LLMGenerationError, GlossaryGenerator, DAGGenerator,
    ModuleDesignGenerator, ModuleSummaryGenerator, SystemDesignGenerator,
    ModuleCritiqueGenerator
)
from docuflow.utils import (
    get_logger, ensure_directory_structure, get_input_files,
    safe_read_text, safe_write_text, safe_read_yaml, safe_write_yaml,
    safe_read_json, safe_write_json, module_name_to_filename, get_timestamp
)

logger = get_logger()


def _get_config(state: DocuFlowState) -> AppConfig:
    """从状态中恢复 AppConfig"""
    return AppConfig.model_validate(state["config"])


def _classify_error(e: Exception) -> str:
    """分类错误类型"""
    if isinstance(e, LLMGenerationError):
        return "retryable" if e.retryable else "permanent"
    if isinstance(e, (TimeoutError, ConnectionError)):
        return "transient"
    return "permanent"


# ============================================================
# Phase 1: 初始化节点
# ============================================================

def load_documents_node(state: DocuFlowState) -> dict[str, Any]:
    """加载并解析输入文档"""
    logger.info("正在加载文档...")
    try:
        config = _get_config(state)

        if not ensure_directory_structure(config):
            return {"error": "无法创建目录结构", "error_type": "permanent"}

        input_files = get_input_files(config.input_dir)
        if not input_files:
            return {"error": f"在 {config.input_dir} 中未找到输入文档", "error_type": "permanent"}

        parser_factory = DocumentParserFactory()
        chunker = DocumentChunker(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)

        combined_content = []
        for file_path in input_files:
            logger.info(f"正在解析: {file_path.name}")
            content = parser_factory.parse(file_path)
            combined_content.append(content)

        full_document = "\n\n---\n\n".join(combined_content)
        chunks = chunker.chunk_with_metadata(full_document, "requirements")

        return {
            "full_document": full_document,
            "chunks": [{"content": c.page_content, "metadata": c.metadata} for c in chunks],
            "error": None,
            "current_phase": "init"
        }
    except Exception as e:
        logger.error(f"加载文档失败: {e}")
        return {"error": str(e), "error_type": _classify_error(e), "failed_node": "load_documents"}


def generate_glossary_node(state: DocuFlowState) -> dict[str, Any]:
    """生成术语表"""
    logger.info("正在生成术语表...")
    try:
        config = _get_config(state)
        full_document = state["full_document"]

        generator = GlossaryGenerator(config)
        glossary = generator.generate(full_document)

        glossary_content = glossary.to_markdown()
        safe_write_text(config.glossary_file, glossary_content)

        return {
            "glossary_content": glossary_content,
            "error": None,
            "retry_count": 0
        }
    except LLMGenerationError as e:
        logger.error(f"术语表生成失败: {e}")
        return {
            "error": str(e),
            "error_type": _classify_error(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "failed_node": "generate_glossary"
        }


def generate_dag_node(state: DocuFlowState) -> dict[str, Any]:
    """生成架构 DAG"""
    logger.info("正在生成架构 DAG...")
    try:
        config = _get_config(state)
        full_document = state["full_document"]
        glossary_content = state["glossary_content"]

        generator = DAGGenerator(config)
        dag = generator.generate(full_document, glossary_content)

        safe_write_json(config.dag_file, dag)

        # 计算拓扑排序
        G = nx.DiGraph()
        for module in dag.modules:
            G.add_node(module.name)
            for dep in module.dependencies:
                G.add_edge(dep, module.name)

        if not nx.is_directed_acyclic_graph(G):
            return {"error": f"架构图包含循环: {list(nx.simple_cycles(G))}", "error_type": "permanent"}

        topo_order = list(nx.topological_sort(G))

        return {
            "dag": dag.model_dump(),
            "topo_order": topo_order,
            "error": None,
            "retry_count": 0
        }
    except LLMGenerationError as e:
        logger.error(f"DAG 生成失败: {e}")
        return {
            "error": str(e),
            "error_type": _classify_error(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "failed_node": "generate_dag"
        }


def initialize_status_node(state: DocuFlowState) -> dict[str, Any]:
    """初始化项目状态"""
    logger.info("正在初始化项目状态...")
    config = _get_config(state)
    dag = ArchitectureDAG.model_validate(state["dag"])

    status = ProjectStatus()
    status.current_phase = "generation"

    for module_def in dag.modules:
        status.modules.append(ModuleProgress(
            name=module_def.name,
            status=ModuleStatus.PENDING,
            dependencies=module_def.dependencies
        ))

    safe_write_yaml(config.status_file, status)

    logger.info("阶段 1 完成！")
    return {
        "status": status.model_dump(),
        "current_phase": "generation",
        "error": None
    }


# ============================================================
# Phase 2: 模块生成节点
# ============================================================

def select_next_module_node(state: DocuFlowState) -> dict[str, Any]:
    """选择下一个要处理的模块（单模块模式，保留兼容性）"""
    status = ProjectStatus.model_validate(state["status"])
    dag = ArchitectureDAG.model_validate(state["dag"])
    topo_order = state["topo_order"]

    status_lookup = {m.name: m.status for m in status.modules}

    for module_name in topo_order:
        if status_lookup.get(module_name) != ModuleStatus.PENDING:
            continue

        module_def = dag.get_module(module_name)
        if module_def and all(
            status_lookup.get(dep) == ModuleStatus.COMPLETED
            for dep in module_def.dependencies
        ):
            logger.info(f"选择模块: {module_name}")
            return {"current_module": module_name, "error": None}

    return {"current_module": None, "error": None}


def find_ready_modules_node(state: DocuFlowState) -> dict[str, Any]:
    """查找所有可并行处理的模块（依赖已满足）"""
    status = ProjectStatus.model_validate(state["status"])
    dag = ArchitectureDAG.model_validate(state["dag"])

    status_lookup = {m.name: m.status for m in status.modules}
    ready_modules = []

    for module in status.modules:
        if module.status != ModuleStatus.PENDING:
            continue

        module_def = dag.get_module(module.name)
        if module_def and all(
            status_lookup.get(dep) == ModuleStatus.COMPLETED
            for dep in module_def.dependencies
        ):
            ready_modules.append(module.name)

    if ready_modules:
        logger.info(f"找到 {len(ready_modules)} 个可并行处理的模块: {ready_modules}")
    return {"ready_modules": ready_modules, "error": None}


def build_context_node(state: DocuFlowState) -> dict[str, Any]:
    """为模块构建 LLM 上下文"""
    config = _get_config(state)
    module_name = state["current_module"]
    dag = ArchitectureDAG.model_validate(state["dag"])

    context = LLMContext()
    context.glossary_content = state.get("glossary_content", "")

    module_def = dag.get_module(module_name)
    if module_def:
        context.module_definition = module_def

        # 加载上游模块内容
        for dep_name in module_def.dependencies:
            dep_file = config.modules_dir / module_name_to_filename(dep_name)
            dep_content = safe_read_text(dep_file)
            if dep_content:
                context.upstream_modules[dep_name] = dep_content

    # 检索相关块
    chunks = state.get("chunks")
    if chunks:
        from langchain_core.documents import Document
        docs = [Document(page_content=c["content"], metadata=c.get("metadata", {})) for c in chunks]
        retriever = ChunkRetriever(docs, method=config.retrieval_method)
        query = f"{module_name} {module_def.description or ''}"
        context.relevant_chunks = retriever.retrieve(query, top_k=config.top_k_chunks)

    return {"module_context": context.model_dump(), "error": None}


def generate_module_design_node(state: DocuFlowState) -> dict[str, Any]:
    """生成模块设计"""
    config = _get_config(state)
    module_name = state["current_module"]

    logger.info(f"正在处理模块: {module_name}")

    # 更新状态为处理中
    status = ProjectStatus.model_validate(state["status"])
    status.update_module_status(module_name, ModuleStatus.PROCESSING)
    safe_write_yaml(config.status_file, status)

    try:
        context = LLMContext.model_validate(state["module_context"])
        generator = ModuleDesignGenerator(config)
        design_content = generator.generate(module_name, context)

        header = f"# 模块设计: {module_name}\n\n生成时间: {get_timestamp()}\n\n---\n\n"
        output_file = config.modules_dir / module_name_to_filename(module_name)
        safe_write_text(output_file, header + design_content)

        return {
            "module_design": design_content,
            "error": None,
            "retry_count": 0
        }
    except LLMGenerationError as e:
        logger.error(f"模块 '{module_name}' 生成失败: {e}")
        return {
            "error": str(e),
            "error_type": _classify_error(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "failed_node": "generate_module_design",
            "failed_module": module_name
        }


def update_module_status_node(state: DocuFlowState) -> dict[str, Any]:
    """更新模块状态"""
    config = _get_config(state)
    module_name = state["current_module"]
    status = ProjectStatus.model_validate(state["status"])

    if state.get("error"):
        status.update_module_status(module_name, ModuleStatus.FAILED, error_message=state["error"])
    else:
        output_file = config.modules_dir / module_name_to_filename(module_name)
        status.update_module_status(
            module_name, ModuleStatus.COMPLETED,
            file_path=str(output_file.relative_to(config.project_root))
        )
        logger.info(f"模块 '{module_name}' 完成")

    safe_write_yaml(config.status_file, status)

    return {
        "status": status.model_dump(),
        "current_module": None,
        "module_context": None,
        "module_design": None,
        "error": None
    }


def skip_failed_module_node(state: DocuFlowState) -> dict[str, Any]:
    """跳过失败的模块"""
    config = _get_config(state)
    module_name = state.get("failed_module") or state.get("current_module")
    status = ProjectStatus.model_validate(state["status"])

    if module_name:
        status.update_module_status(module_name, ModuleStatus.FAILED, error_message=state.get("error"))
        safe_write_yaml(config.status_file, status)
        logger.warning(f"跳过失败的模块: {module_name}")

    return {
        "status": status.model_dump(),
        "current_module": None,
        "error": None,
        "retry_count": 0
    }


def process_single_module_node(state: DocuFlowState) -> dict[str, Any]:
    """处理单个模块（并行执行时使用）- 包含构建上下文、生成设计、批判循环、更新状态"""
    config = _get_config(state)
    module_name = state["current_module"]
    dag = ArchitectureDAG.model_validate(state["dag"])

    logger.info(f"[并行] 正在处理模块: {module_name}")

    try:
        # 1. 构建上下文
        context = LLMContext()
        context.glossary_content = state.get("glossary_content", "")

        module_def = dag.get_module(module_name)
        if module_def:
            context.module_definition = module_def

            # 加载上游模块内容
            for dep_name in module_def.dependencies:
                dep_file = config.modules_dir / module_name_to_filename(dep_name)
                dep_content = safe_read_text(dep_file)
                if dep_content:
                    context.upstream_modules[dep_name] = dep_content

        # 检索相关块
        chunks = state.get("chunks")
        if chunks:
            from langchain_core.documents import Document
            docs = [Document(page_content=c["content"], metadata=c.get("metadata", {})) for c in chunks]
            retriever = ChunkRetriever(docs, method=config.retrieval_method)
            query = f"{module_name} {module_def.description or '' if module_def else ''}"
            context.relevant_chunks = retriever.retrieve(query, top_k=config.top_k_chunks)

        # 2. 生成设计
        generator = ModuleDesignGenerator(config)
        design_content = generator.generate(module_name, context)

        # 3. 批判循环（如果启用）
        critique_iterations = 0
        final_score = None
        final_passed = True
        last_suggestions = None
        critique_history = []

        if config.critique_enabled:
            critique_gen = ModuleCritiqueGenerator(config)
            for i in range(config.critique_max_iterations):
                result = critique_gen.critique(
                    module_name, design_content, context, config.critique_threshold
                )
                critique_iterations = i + 1
                final_score = result.get("score", 0)
                final_passed = result.get("passed", False)
                last_suggestions = result.get("suggestions")

                # 保存批判日志
                log_entry = CritiqueLogEntry(
                    iteration=critique_iterations,
                    module_name=module_name,
                    score=final_score,
                    passed=final_passed,
                    suggestions=last_suggestions,
                    issues=result.get("issues", []),
                    design_content=design_content
                )
                _save_critique_log(config, module_name, log_entry)

                # 记录历史
                critique_history.append({
                    "iteration": critique_iterations,
                    "score": final_score,
                    "passed": final_passed
                })

                if final_passed:
                    logger.info(f"[并行] 模块 '{module_name}' 批判通过 (迭代 {critique_iterations}, 分数 {final_score:.2f})")
                    break
                if i < config.critique_max_iterations - 1:
                    logger.info(f"[并行] 模块 '{module_name}' 批判未通过，正在改进 (迭代 {critique_iterations})")
                    design_content = generator.regenerate(
                        module_name, design_content, result, context, config.critique_threshold
                    )
                else:
                    logger.warning(f"[并行] 模块 '{module_name}' 达到最大批判迭代次数，使用最终版本")

        # 4. 保存文件
        iteration_info = f"\n批判迭代: {critique_iterations}" if config.critique_enabled and critique_iterations > 0 else ""
        header = f"# 模块设计: {module_name}\n\n生成时间: {get_timestamp()}{iteration_info}\n\n---\n\n"
        output_file = config.modules_dir / module_name_to_filename(module_name)
        safe_write_text(output_file, header + design_content)

        logger.info(f"[并行] 模块 '{module_name}' 生成完成")

        return {
            "completed_modules_batch": {
                "current_module": module_name,
                "module_design": design_content,
                "error": None,
                "file_path": str(output_file.relative_to(config.project_root)),
                "critique_iterations": critique_iterations,
                "final_score": final_score,
                "critique_passed": final_passed,
                "critique_suggestions": last_suggestions,
                "critique_history": critique_history
            }
        }

    except LLMGenerationError as e:
        logger.error(f"[并行] 模块 '{module_name}' 生成失败: {e}")
        return {
            "completed_modules_batch": {
                "current_module": module_name,
                "error": str(e),
                "error_type": _classify_error(e)
            }
        }


def collect_parallel_results_node(state: DocuFlowState) -> dict[str, Any]:
    """收集并行处理的结果，更新状态"""
    config = _get_config(state)
    status = ProjectStatus.model_validate(state["status"])
    results = state.get("completed_modules_batch", [])

    for result in results:
        module_name = result.get("current_module")
        if not module_name:
            continue

        if result.get("error"):
            status.update_module_status(
                module_name, ModuleStatus.FAILED,
                error_message=result.get("error")
            )
            logger.warning(f"模块 '{module_name}' 失败: {result.get('error')}")
        else:
            status.update_module_status(
                module_name, ModuleStatus.COMPLETED,
                file_path=result.get("file_path")
            )
            logger.info(f"模块 '{module_name}' 完成")

    safe_write_yaml(config.status_file, status)

    return {
        "status": status.model_dump(),
        "ready_modules": None,
        "completed_modules_batch": None,
        "current_module": None,
        "error": None
    }


# ============================================================
# Phase 3: 系统概述节点
# ============================================================

def extract_summaries_node(state: DocuFlowState) -> dict[str, Any]:
    """提取模块摘要"""
    logger.info("正在提取模块摘要...")
    config = _get_config(state)
    topo_order = state["topo_order"]

    try:
        generator = ModuleSummaryGenerator(config)
        summaries = []

        for module_name in topo_order:
            module_file = config.modules_dir / module_name_to_filename(module_name)
            content = safe_read_text(module_file)
            if content:
                summary = generator.generate(module_name, content)
                summaries.append(summary)

        return {"module_summaries": summaries, "error": None, "retry_count": 0}
    except LLMGenerationError as e:
        logger.error(f"摘要提取失败: {e}")
        return {
            "error": str(e),
            "error_type": _classify_error(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "failed_node": "extract_summaries"
        }


def _format_summaries(summaries: list[dict]) -> str:
    """将模块摘要列表格式化为用于系统级汇总的 Markdown 文本。"""
    if not summaries:
        return ""

    lines: list[str] = []
    for summary in summaries:
        module_name = summary.get("module_name") or "未知模块"
        lines.append(f"### 模块：{module_name}")

        purpose = (summary.get("purpose") or "").strip()
        if purpose:
            lines.append(f"- 职责：{purpose}")

        if features := (summary.get("key_features") or []):
            lines.append("- 核心功能：")
            for feat in features[:8]:
                lines.append(f"  - {feat}")

        if apis := (summary.get("interfaces") or []):
            lines.append("- 主要接口：")
            for api in apis[:12]:
                method = (api.get("method") or "GET").strip()
                path = (api.get("path") or "/").strip()
                desc = (api.get("description") or "").strip()
                line = f"  - {method} {path}"
                if desc:
                    line += f" - {desc}"
                lines.append(line)

        if tables := (summary.get("database_tables") or []):
            lines.append("- 数据表：")
            for table in tables[:12]:
                name = (table.get("name") or "").strip()
                desc = (table.get("description") or "").strip()
                if not name:
                    continue
                line = f"  - {name}"
                if desc:
                    line += f" - {desc}"
                lines.append(line)

        if deps := (summary.get("dependencies") or []):
            lines.append(f"- 依赖：{', '.join(deps)}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _format_dag_overview(dag: dict | None) -> str:
    """将架构 DAG 压缩为系统级提示可读的概览文本。"""
    if not dag:
        return ""
    modules = dag.get("modules") or []
    if not isinstance(modules, list) or not modules:
        return ""

    lines = ["- 模块依赖（DAG 概览）："]
    for m in modules:
        if not isinstance(m, dict):
            continue
        name = (m.get("name") or "").strip()
        if not name:
            continue
        desc = (m.get("description") or "").strip()
        deps = m.get("dependencies") or []
        deps_text = ", ".join(deps) if isinstance(deps, list) and deps else "无"
        if desc:
            lines.append(f"  - {name}: {desc}（依赖：{deps_text}）")
        else:
            lines.append(f"  - {name}（依赖：{deps_text}）")
    return "\n".join(lines).strip() + "\n"


def generate_system_design_node(state: DocuFlowState) -> dict[str, Any]:
    """生成系统设计"""
    logger.info("正在生成系统设计...")
    config = _get_config(state)

    try:
        generator = SystemDesignGenerator(config)
        summaries_text = _format_summaries(state.get("module_summaries") or [])
        dag_overview = _format_dag_overview(state.get("dag"))
        glossary_excerpt = (state.get("glossary_content") or "")[:20000]
        requirements_excerpt = (state.get("full_document") or "")[:20000]

        system_design = generator.generate_system_design(
            summaries_text,
            dag_overview=dag_overview,
            glossary_excerpt=glossary_excerpt,
            requirements_excerpt=requirements_excerpt,
        )
        safe_write_text(config.global_dir / "system_design.md", system_design)

        return {"system_design": system_design, "error": None, "retry_count": 0}
    except LLMGenerationError as e:
        logger.error(f"系统设计生成失败: {e}")
        return {
            "error": str(e),
            "error_type": _classify_error(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "failed_node": "generate_system_design"
        }


def generate_interface_design_node(state: DocuFlowState) -> dict[str, Any]:
    """生成接口设计"""
    logger.info("正在生成接口设计...")
    config = _get_config(state)

    try:
        generator = SystemDesignGenerator(config)
        summaries_text = _format_summaries(state.get("module_summaries") or [])
        dag_overview = _format_dag_overview(state.get("dag"))
        glossary_excerpt = (state.get("glossary_content") or "")[:20000]
        requirements_excerpt = (state.get("full_document") or "")[:20000]

        interface_design = generator.generate_interface_design(
            summaries_text,
            dag_overview=dag_overview,
            glossary_excerpt=glossary_excerpt,
            requirements_excerpt=requirements_excerpt,
        )
        safe_write_text(config.global_dir / "interface_design.md", interface_design)

        return {"interface_design": interface_design, "error": None, "retry_count": 0}
    except LLMGenerationError as e:
        logger.error(f"接口设计生成失败: {e}")
        return {
            "error": str(e),
            "error_type": _classify_error(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "failed_node": "generate_interface_design"
        }


def generate_database_design_node(state: DocuFlowState) -> dict[str, Any]:
    """生成数据库设计"""
    logger.info("正在生成数据库设计...")
    config = _get_config(state)

    try:
        generator = SystemDesignGenerator(config)
        summaries_text = _format_summaries(state.get("module_summaries") or [])
        dag_overview = _format_dag_overview(state.get("dag"))
        glossary_excerpt = (state.get("glossary_content") or "")[:20000]
        requirements_excerpt = (state.get("full_document") or "")[:20000]

        database_design = generator.generate_database_design(
            summaries_text,
            dag_overview=dag_overview,
            glossary_excerpt=glossary_excerpt,
            requirements_excerpt=requirements_excerpt,
        )
        safe_write_text(config.global_dir / "database_design.md", database_design)

        # 保存摘要 JSON
        safe_write_text(
            config.global_dir / "module_summaries.json",
            json.dumps(state["module_summaries"], ensure_ascii=False, indent=2)
        )

        return {
            "database_design": database_design,
            "current_phase": "assembly",
            "error": None,
            "retry_count": 0
        }
    except LLMGenerationError as e:
        logger.error(f"数据库设计生成失败: {e}")
        return {
            "error": str(e),
            "error_type": _classify_error(e),
            "retry_count": state.get("retry_count", 0) + 1,
            "failed_node": "generate_database_design"
        }


# ============================================================
# Phase 4: 组装节点
# ============================================================

def _slugify(text: str) -> str:
    """将文本转换为 Markdown 锚点格式

    GitHub/CommonMark 锚点规则:
    - 转小写
    - 移除除字母、数字、空格、连字符外的所有字符
    - 空格替换为连字符
    - 连续连字符合并为一个

    对于中文等非 ASCII 字符，使用 hash 作为备选方案
    """
    import re
    import hashlib

    original_text = text
    # 转小写
    text = text.lower()
    # 保留字母、数字、空格、连字符、中文字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', text, flags=re.UNICODE)
    # 空格和下划线替换为连字符
    text = re.sub(r'[\s_]+', '-', text)
    # 合并连续连字符
    text = re.sub(r'-+', '-', text)
    # 去除首尾连字符
    text = text.strip('-')

    # 如果 slugify 后为空（全是特殊字符），使用 hash
    if not text:
        text = hashlib.md5(original_text.encode()).hexdigest()[:8]

    return text


def assemble_document_node(state: DocuFlowState) -> dict[str, Any]:
    """组装最终文档"""
    logger.info("正在组装最终文档...")
    config = _get_config(state)
    status = ProjectStatus.model_validate(state["status"])
    topo_order = state["topo_order"]

    # 不再使用 slugify 生成锚点，改用纯数字索引
    sections = [
        f"# {status.project_name} - 软件设计文档\n",
        f"生成时间: {get_timestamp()}\n",
        "\n## 目录\n",
        "1. [概述说明](#1-概述说明)\n",
        "   - 1.1 [术语与缩略词](#11-术语与缩略词)\n",
        "2. [系统设计](#2-系统设计)\n",
        "3. [模块设计](#3-模块设计)\n",
    ]

    # 模块目录使用纯数字锚点，避免中文编码问题
    for i, name in enumerate(topo_order, 1):
        sections.append(f"   - 3.{i} [{name}](#module-{i})\n")

    sections.append("4. [接口设计](#4-接口设计)\n")
    sections.append("5. [数据库设计](#5-数据库设计)\n")

    # 1. 概述
    sections.append("\n---\n# 1 概述说明\n\n## 1.1 术语与缩略词\n")
    glossary = state.get("glossary_content", "")
    for line in glossary.split('\n'):
        if not line.startswith('# '):
            sections.append(line + "\n")

    # 2. 系统设计
    sections.append("\n---\n# 2 系统设计\n")
    sections.append(state.get("system_design") or safe_read_text(config.global_dir / "system_design.md") or "*待生成*\n")

    # 3. 模块设计
    sections.append("\n---\n# 3 模块设计\n")
    for i, name in enumerate(topo_order, 1):
        # 使用纯数字锚点
        anchor_id = f"module-{i}"
        sections.append(f"\n<a id=\"{anchor_id}\"></a>\n")
        sections.append(f"\n## 3.{i} {name}\n\n")
        content = safe_read_text(config.modules_dir / module_name_to_filename(name))
        if content:
            # 需要跳过的头部行
            skip_prefixes = ('# 模块设计:', '# ', '生成时间:', '批判迭代:', '---')
            for line in content.split('\n'):
                # 跳过头部元信息
                if any(line.startswith(prefix) for prefix in skip_prefixes):
                    continue
                # 将模块内的 ## 转换为 ###，### 转换为 ####
                # 这样模块内部的章节就不会与模块标题同级
                if line.startswith('## '):
                    line = '#' + line  # ## -> ###
                elif line.startswith('### '):
                    line = '#' + line  # ### -> ####
                sections.append(line + "\n")

    # 4. 接口设计
    sections.append("\n---\n# 4 接口设计\n")
    sections.append(state.get("interface_design") or safe_read_text(config.global_dir / "interface_design.md") or "*待生成*\n")

    # 5. 数据库设计
    sections.append("\n---\n# 5 数据库设计\n")
    sections.append(state.get("database_design") or safe_read_text(config.global_dir / "database_design.md") or "*待生成*\n")

    output_file = config.output_dir / "final_design_document.md"
    if not safe_write_text(output_file, "".join(sections)):
        return {"error": "无法写入最终文档", "error_type": "permanent"}

    # 更新状态
    status.current_phase = "completed"
    safe_write_yaml(config.status_file, status)

    logger.info(f"最终文档: {output_file}")
    return {
        "final_document_path": str(output_file),
        "current_phase": "completed",
        "status": status.model_dump(),
        "error": None
    }


# ============================================================
# 辅助节点
# ============================================================

def backoff_delay_node(state: DocuFlowState) -> dict[str, Any]:
    """指数退避延迟"""
    import time
    retry_count = state.get("retry_count", 0)
    delay = min(2 ** retry_count, 30)  # 最大 30 秒
    logger.info(f"第 {retry_count} 次重试，延迟 {delay} 秒...")
    time.sleep(delay)
    return {}


# ============================================================
# 批判节点
# ============================================================

def _save_critique_log(config: AppConfig, module_name: str, log_entry: CritiqueLogEntry) -> None:
    """保存批判日志到文件"""
    import os
    from docuflow.utils import module_name_to_filename

    # 确保日志目录存在
    logs_dir = config.critique_logs_dir
    os.makedirs(logs_dir, exist_ok=True)

    # 模块对应的日志文件
    log_file = logs_dir / f"{module_name_to_filename(module_name).replace('.md', '')}_critique.md"

    # 如果文件不存在，创建头部
    if not log_file.exists():
        header = f"# 批判日志: {module_name}\n\n"
        safe_write_text(log_file, header)

    # 追加本次批判记录
    content = safe_read_text(log_file) or ""
    content += log_entry.to_markdown() + "\n"
    safe_write_text(log_file, content)

    logger.info(f"批判日志已保存: {log_file}")

def critique_module_node(state: DocuFlowState) -> dict[str, Any]:
    """批判模块设计"""
    config = _get_config(state)

    # 如果批判功能未启用，直接通过
    if not config.critique_enabled:
        return {"critique_result": {"passed": True, "score": 1.0}, "error": None}

    module_name = state["current_module"]
    iteration = state.get("critique_iteration", 0)

    # 达到最大迭代次数，强制通过
    if iteration >= config.critique_max_iterations:
        logger.warning(f"模块 '{module_name}' 达到最大批判次数，强制通过")
        return {"critique_result": {"passed": True, "score": config.critique_threshold}, "error": None}

    try:
        context = LLMContext.model_validate(state["module_context"])
        generator = ModuleCritiqueGenerator(config)
        result = generator.critique(
            module_name, state["module_design"], context, config.critique_threshold
        )

        # 创建批判日志条目
        log_entry = CritiqueLogEntry(
            iteration=iteration + 1,
            module_name=module_name,
            score=result.get("score", 0),
            passed=result.get("passed", False),
            suggestions=result.get("suggestions"),
            issues=result.get("issues", []),
            design_content=state["module_design"]
        )

        # 保存批判日志到文件
        _save_critique_log(config, module_name, log_entry)

        # 记录历史
        history = state.get("critique_history") or []
        history.append({"iteration": iteration + 1, "score": result.get("score", 0)})

        # 保存原始设计（仅首次）
        original = state.get("original_module_design") or state["module_design"]

        return {
            "critique_result": result,
            "critique_iteration": iteration + 1,
            "critique_history": history,
            "original_module_design": original,
            "error": None
        }
    except LLMGenerationError as e:
        logger.error(f"模块 '{module_name}' 批判失败: {e}")
        return {"error": str(e), "error_type": _classify_error(e)}


def regenerate_module_node(state: DocuFlowState) -> dict[str, Any]:
    """根据批判反馈重新生成模块设计"""
    config = _get_config(state)
    module_name = state["current_module"]
    iteration = state.get("critique_iteration", 1)

    logger.info(f"正在根据反馈重新生成模块设计: {module_name} (迭代 {iteration})")

    try:
        context = LLMContext.model_validate(state["module_context"])
        generator = ModuleDesignGenerator(config)

        new_design = generator.regenerate(
            module_name, state["module_design"],
            state["critique_result"], context, config.critique_threshold
        )

        # 更新文件
        header = f"# 模块设计: {module_name}\n\n生成时间: {get_timestamp()}\n批判迭代: {iteration}\n\n---\n\n"
        output_file = config.modules_dir / module_name_to_filename(module_name)
        safe_write_text(output_file, header + new_design)

        return {"module_design": new_design, "error": None}
    except LLMGenerationError as e:
        logger.error(f"模块 '{module_name}' 重新生成失败: {e}")
        return {"error": str(e), "error_type": _classify_error(e)}


def reset_critique_state_node(state: DocuFlowState) -> dict[str, Any]:
    """重置批判状态，准备处理下一个模块"""
    return {
        "critique_result": None,
        "critique_iteration": 0,
        "critique_history": None,
        "original_module_design": None
    }
