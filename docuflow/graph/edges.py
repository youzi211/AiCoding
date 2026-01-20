"""LangGraph 路由逻辑"""
from langgraph.types import Send

from docuflow.graph.state import DocuFlowState
from docuflow.core.models import ProjectStatus, ModuleStatus


def module_router(state: DocuFlowState) -> str:
    """
    模块路由器：决定下一步操作

    Returns:
        - "select_next_module": 有待处理模块
        - "extract_summaries": 所有模块完成，进入概览阶段
    """
    status = ProjectStatus.model_validate(state["status"])
    pending = [m for m in status.modules if m.status == ModuleStatus.PENDING]

    if pending:
        return "select_next_module"
    return "extract_summaries"


def parallel_module_router(state: DocuFlowState) -> list[Send] | str:
    """
    并行模块路由器：使用 Send 分发并行任务

    Returns:
        - list[Send]: 分发多个并行任务
        - "extract_summaries": 所有模块完成
    """
    ready_modules = state.get("ready_modules", [])

    if not ready_modules:
        return "extract_summaries"

    # 使用 Send 分发并行任务
    return [
        Send("process_single_module", {**state, "current_module": module_name})
        for module_name in ready_modules
    ]


def generation_router(state: DocuFlowState) -> str:
    """
    生成路由器：模块生成后的路由

    Returns:
        - "update_module_status": 继续处理
        - "backoff_delay": 需要重试
        - "skip_failed_module": 跳过失败的模块
    """
    error = state.get("error")
    if not error:
        return "update_module_status"

    error_type = state.get("error_type", "permanent")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("config", {}).get("max_retries", 3)

    if error_type == "permanent":
        return "skip_failed_module"

    if retry_count < max_retries:
        return "backoff_delay"

    return "skip_failed_module"


def overview_router(state: DocuFlowState) -> str:
    """
    概览路由器：概览生成后的路由

    Returns:
        - "generate_interface_design": 继续生成
        - "backoff_delay": 需要重试
        - "assemble_document": 跳过继续
    """
    error = state.get("error")
    if not error:
        return "continue"

    retry_count = state.get("retry_count", 0)
    max_retries = state.get("config", {}).get("max_retries", 3)

    if retry_count < max_retries:
        return "backoff_delay"

    return "continue"  # 即使失败也继续


def step_mode_router(state: DocuFlowState) -> str:
    """
    步进模式路由器：检查是否需要暂停

    Returns:
        - "pause": 步进模式下暂停
        - "continue": 继续处理
    """
    if state.get("step_by_step_mode") and state.get("current_module"):
        return "pause"
    return "continue"


def critique_router(state: DocuFlowState) -> str:
    """
    批判路由器：批判后决定下一步操作

    Returns:
        - "reset_critique_state": 批判通过，继续处理
        - "regenerate_module": 批判未通过且未超限，重新生成
        - "backoff_delay": 发生错误需要重试
        - "skip_failed_module": 永久性错误，跳过
    """
    # 检查错误
    error = state.get("error")
    if error:
        error_type = state.get("error_type", "permanent")
        if error_type == "permanent":
            return "skip_failed_module"
        return "backoff_delay"

    # 检查批判结果
    result = state.get("critique_result", {})
    if result.get("passed", True):
        return "reset_critique_state"

    # 检查迭代次数
    iteration = state.get("critique_iteration", 0)
    max_iter = state.get("config", {}).get("critique_max_iterations", 2)
    if iteration >= max_iter:
        return "reset_critique_state"

    return "regenerate_module"
