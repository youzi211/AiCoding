"""LangGraph 图构建"""
from langgraph.graph import StateGraph, END

from docuflow.graph.state import DocuFlowState
from docuflow.graph.nodes import (
    load_documents_node,
    generate_glossary_node,
    generate_dag_node,
    initialize_status_node,
    select_next_module_node,
    build_context_node,
    generate_module_design_node,
    update_module_status_node,
    skip_failed_module_node,
    extract_summaries_node,
    generate_system_design_node,
    generate_interface_design_node,
    generate_database_design_node,
    assemble_document_node,
    backoff_delay_node,
    find_ready_modules_node,
    process_single_module_node,
    collect_parallel_results_node,
    critique_module_node,
    regenerate_module_node,
    reset_critique_state_node,
)
from docuflow.graph.edges import module_router, generation_router, parallel_module_router, critique_router


def build_graph() -> StateGraph:
    """构建 DocuFlow StateGraph"""
    workflow = StateGraph(DocuFlowState)

    # ============================================================
    # Phase 1: 初始化节点
    # ============================================================
    workflow.add_node("load_documents", load_documents_node)
    workflow.add_node("generate_glossary", generate_glossary_node)
    workflow.add_node("generate_dag", generate_dag_node)
    workflow.add_node("initialize_status", initialize_status_node)

    # ============================================================
    # Phase 2: 模块生成节点
    # ============================================================
    workflow.add_node("select_next_module", select_next_module_node)
    workflow.add_node("build_context", build_context_node)
    workflow.add_node("generate_module_design", generate_module_design_node)
    workflow.add_node("update_module_status", update_module_status_node)
    workflow.add_node("skip_failed_module", skip_failed_module_node)
    workflow.add_node("backoff_delay", backoff_delay_node)

    # 批判节点
    workflow.add_node("critique_module", critique_module_node)
    workflow.add_node("regenerate_module", regenerate_module_node)
    workflow.add_node("reset_critique_state", reset_critique_state_node)

    # ============================================================
    # Phase 3: 系统概述节点
    # ============================================================
    workflow.add_node("extract_summaries", extract_summaries_node)
    workflow.add_node("generate_system_design", generate_system_design_node)
    workflow.add_node("generate_interface_design", generate_interface_design_node)
    workflow.add_node("generate_database_design", generate_database_design_node)

    # ============================================================
    # Phase 4: 组装节点
    # ============================================================
    workflow.add_node("assemble_document", assemble_document_node)

    # ============================================================
    # 边定义
    # ============================================================

    # Phase 1: 初始化流程
    workflow.set_entry_point("load_documents")
    workflow.add_edge("load_documents", "generate_glossary")
    workflow.add_edge("generate_glossary", "generate_dag")
    workflow.add_edge("generate_dag", "initialize_status")

    # Phase 2: 模块生成循环
    workflow.add_conditional_edges(
        "initialize_status",
        module_router,
        {
            "select_next_module": "select_next_module",
            "extract_summaries": "extract_summaries"
        }
    )

    workflow.add_edge("select_next_module", "build_context")
    workflow.add_edge("build_context", "generate_module_design")

    # 模块生成后的路由 → 批判节点
    workflow.add_conditional_edges(
        "generate_module_design",
        generation_router,
        {
            "update_module_status": "critique_module",  # 成功后进入批判
            "backoff_delay": "backoff_delay",
            "skip_failed_module": "skip_failed_module"
        }
    )

    # 批判后的路由
    workflow.add_conditional_edges(
        "critique_module",
        critique_router,
        {
            "reset_critique_state": "reset_critique_state",
            "regenerate_module": "regenerate_module",
            "backoff_delay": "backoff_delay",
            "skip_failed_module": "skip_failed_module"
        }
    )

    # 重新生成后再次批判
    workflow.add_edge("regenerate_module", "critique_module")

    # 重置批判状态后更新模块状态
    workflow.add_edge("reset_critique_state", "update_module_status")

    # 重试循环
    workflow.add_edge("backoff_delay", "generate_module_design")

    # 跳过失败模块后继续
    workflow.add_conditional_edges(
        "skip_failed_module",
        module_router,
        {
            "select_next_module": "select_next_module",
            "extract_summaries": "extract_summaries"
        }
    )

    # 更新状态后继续
    workflow.add_conditional_edges(
        "update_module_status",
        module_router,
        {
            "select_next_module": "select_next_module",
            "extract_summaries": "extract_summaries"
        }
    )

    # Phase 3: 系统概述流程
    workflow.add_edge("extract_summaries", "generate_system_design")
    workflow.add_edge("generate_system_design", "generate_interface_design")
    workflow.add_edge("generate_interface_design", "generate_database_design")

    # Phase 4: 组装
    workflow.add_edge("generate_database_design", "assemble_document")
    workflow.add_edge("assemble_document", END)

    return workflow


def build_init_graph() -> StateGraph:
    """构建仅初始化阶段的图"""
    workflow = StateGraph(DocuFlowState)

    workflow.add_node("load_documents", load_documents_node)
    workflow.add_node("generate_glossary", generate_glossary_node)
    workflow.add_node("generate_dag", generate_dag_node)
    workflow.add_node("initialize_status", initialize_status_node)

    workflow.set_entry_point("load_documents")
    workflow.add_edge("load_documents", "generate_glossary")
    workflow.add_edge("generate_glossary", "generate_dag")
    workflow.add_edge("generate_dag", "initialize_status")
    workflow.add_edge("initialize_status", END)

    return workflow


def build_generation_graph() -> StateGraph:
    """构建并行模块生成阶段的图

    使用 LangGraph Send API 实现并行处理:
    1. find_ready_modules: 查找所有依赖已满足的模块
    2. parallel_module_router: 使用 Send 分发并行任务
    3. process_single_module: 并行处理每个模块
    4. collect_parallel_results: 收集结果，更新状态
    5. 循环直到所有模块完成
    """
    workflow = StateGraph(DocuFlowState)

    # 添加节点
    workflow.add_node("find_ready_modules", find_ready_modules_node)
    workflow.add_node("process_single_module", process_single_module_node)
    workflow.add_node("collect_parallel_results", collect_parallel_results_node)

    # 入口点：查找就绪模块
    workflow.set_entry_point("find_ready_modules")

    # 条件路由：分发并行任务或结束
    workflow.add_conditional_edges(
        "find_ready_modules",
        parallel_module_router,
        ["process_single_module", "extract_summaries"]
    )

    # 并行处理后收集结果（所有并行任务完成后汇聚到此）
    workflow.add_edge("process_single_module", "collect_parallel_results")

    # 收集结果后继续查找下一批就绪模块
    workflow.add_edge("collect_parallel_results", "find_ready_modules")

    # extract_summaries 作为终点（实际不执行，只是路由目标）
    workflow.add_node("extract_summaries", lambda s: {})
    workflow.add_edge("extract_summaries", END)

    return workflow


def build_overview_graph() -> StateGraph:
    """构建仅系统概述阶段的图"""
    workflow = StateGraph(DocuFlowState)

    workflow.add_node("extract_summaries", extract_summaries_node)
    workflow.add_node("generate_system_design", generate_system_design_node)
    workflow.add_node("generate_interface_design", generate_interface_design_node)
    workflow.add_node("generate_database_design", generate_database_design_node)

    workflow.set_entry_point("extract_summaries")
    workflow.add_edge("extract_summaries", "generate_system_design")
    workflow.add_edge("generate_system_design", "generate_interface_design")
    workflow.add_edge("generate_interface_design", "generate_database_design")
    workflow.add_edge("generate_database_design", END)

    return workflow


def build_assembly_graph() -> StateGraph:
    """构建仅组装阶段的图"""
    workflow = StateGraph(DocuFlowState)

    workflow.add_node("assemble_document", assemble_document_node)

    workflow.set_entry_point("assemble_document")
    workflow.add_edge("assemble_document", END)

    return workflow
