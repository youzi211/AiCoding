"""LangGraph 状态模式定义"""
from typing import TypedDict, Optional, Any, Annotated


def merge_module_results(existing: list[dict] | None, new: list[dict] | dict | None) -> list[dict]:
    """合并并行模块处理结果"""
    if existing is None:
        existing = []
    if new is None:
        return existing
    if isinstance(new, dict):
        return existing + [new]
    return existing + new


class DocuFlowState(TypedDict, total=False):
    """LangGraph 状态定义"""
    # 配置
    config: dict[str, Any]

    # Phase 1: 文档加载
    full_document: Optional[str]
    chunks: Optional[list[dict]]

    # Phase 2: 初始化
    glossary_content: Optional[str]
    dag: Optional[dict]
    topo_order: Optional[list[str]]

    # Phase 3: 状态跟踪
    status: Optional[dict]

    # Phase 4: 模块处理
    current_module: Optional[str]
    module_context: Optional[dict]
    module_design: Optional[str]

    # 并行执行支持
    ready_modules: Optional[list[str]]  # 当前可并行处理的模块列表
    completed_modules_batch: Annotated[list[dict], merge_module_results]  # 使用 reducer 收集并行结果

    # Phase 5: 摘要和系统设计
    module_summaries: Optional[list[dict]]
    system_design: Optional[str]
    interface_design: Optional[str]
    database_design: Optional[str]

    # Phase 6: 组装
    final_document_path: Optional[str]

    # 错误处理
    error: Optional[str]
    error_type: Optional[str]  # "transient", "retryable", "permanent"
    retry_count: int
    failed_node: Optional[str]
    failed_module: Optional[str]

    # 控制流
    step_by_step_mode: bool
    current_phase: str
