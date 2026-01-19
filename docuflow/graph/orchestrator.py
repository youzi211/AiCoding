"""LangGraph 编排器"""
from typing import Optional

import networkx as nx
from langgraph.checkpoint.memory import MemorySaver

from docuflow.core.models import (
    AppConfig, ProjectStatus, ModuleStatus, ArchitectureDAG
)
from docuflow.graph.state import DocuFlowState
from docuflow.graph.builder import (
    build_init_graph, build_generation_graph,
    build_overview_graph, build_assembly_graph
)
from docuflow.utils import (
    get_logger, safe_read_yaml, safe_write_yaml,
    safe_read_json, safe_read_text
)


class WorkflowOrchestrator:
    """基于 LangGraph 的工作流编排器"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = get_logger()
        self.checkpointer = MemorySaver()

    def _build_initial_state(self) -> DocuFlowState:
        """构建初始状态"""
        return {
            "config": self.config.model_dump(mode="json"),
            "full_document": None,
            "chunks": None,
            "glossary_content": None,
            "dag": None,
            "topo_order": None,
            "status": None,
            "current_module": None,
            "module_context": None,
            "module_design": None,
            "ready_modules": None,
            "completed_modules_batch": [],
            "module_summaries": None,
            "system_design": None,
            "interface_design": None,
            "database_design": None,
            "final_document_path": None,
            "error": None,
            "error_type": None,
            "retry_count": 0,
            "failed_node": None,
            "failed_module": None,
            "step_by_step_mode": False,
            "current_phase": "init"
        }

    def _load_existing_state(self) -> DocuFlowState:
        """加载现有状态"""
        state = self._build_initial_state()

        # 加载状态文件
        status = safe_read_yaml(self.config.status_file, ProjectStatus)
        if status:
            state["status"] = status.model_dump()
            state["current_phase"] = status.current_phase

        # 加载 DAG
        dag = safe_read_json(self.config.dag_file, ArchitectureDAG)
        if dag:
            state["dag"] = dag.model_dump()
            # 重建拓扑序
            G = nx.DiGraph()
            for module in dag.modules:
                G.add_node(module.name)
                for dep in module.dependencies:
                    G.add_edge(dep, module.name)
            state["topo_order"] = list(nx.topological_sort(G))

        # 加载术语表
        glossary = safe_read_text(self.config.glossary_file)
        if glossary:
            state["glossary_content"] = glossary

        return state

    def run_init(self) -> bool:
        """阶段 1：初始化"""
        self.logger.info("=== 阶段 1：初始化 ===")

        graph = build_init_graph()
        app = graph.compile(checkpointer=self.checkpointer)

        initial_state = self._build_initial_state()
        config = {"configurable": {"thread_id": "init"}}

        try:
            result = app.invoke(initial_state, config)

            if result.get("error"):
                self.logger.error(f"初始化失败: {result['error']}")
                return False

            self.logger.info("阶段 1 完成！")
            return True
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            return False

    def run_generation(self, step_by_step: Optional[bool] = None) -> bool:
        """阶段 2：并行拓扑生成

        使用 LangGraph Send API 实现并行处理:
        - 同时处理所有依赖已满足的模块
        - 批次完成后自动查找下一批可处理模块
        - 循环直到所有模块完成
        """
        self.logger.info("=== 阶段 2：并行拓扑生成 ===")

        state = self._load_existing_state()
        if not state.get("dag"):
            self.logger.error("请先运行 'init' 命令")
            return False

        state["step_by_step_mode"] = step_by_step or False
        state["completed_modules_batch"] = []  # 初始化并行结果收集器

        graph = build_generation_graph()
        app = graph.compile(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": "generation"}}

        try:
            # 并行图会自动循环处理所有模块直到完成
            result = app.invoke(state, config)

            if result.get("error") and result.get("error_type") == "permanent":
                self.logger.error(f"生成失败: {result['error']}")
                return False

            # 重新加载状态检查完成情况
            status = safe_read_yaml(self.config.status_file, ProjectStatus)
            completed = sum(1 for m in status.modules if m.status == ModuleStatus.COMPLETED)
            failed = sum(1 for m in status.modules if m.status == ModuleStatus.FAILED)
            total = len(status.modules)

            self.logger.info(f"模块处理完成: {completed}/{total} 成功, {failed} 失败")

            # 更新阶段
            status.current_phase = "overview"
            safe_write_yaml(self.config.status_file, status)

            return True

        except Exception as e:
            self.logger.error(f"生成失败: {e}")
            return False

    def run_overview(self) -> bool:
        """阶段 3：生成系统概述"""
        self.logger.info("=== 阶段 3：系统概述生成 ===")

        state = self._load_existing_state()
        if not state.get("dag"):
            self.logger.error("请先运行 'init' 命令")
            return False

        # 检查是否有待处理模块
        status = ProjectStatus.model_validate(state["status"])
        pending_count = sum(1 for m in status.modules if m.status == ModuleStatus.PENDING)
        if pending_count > 0:
            self.logger.error("还有模块待处理，请先运行 'run' 命令")
            return False

        graph = build_overview_graph()
        app = graph.compile(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": "overview"}}

        try:
            result = app.invoke(state, config)

            if result.get("error") and result.get("error_type") == "permanent":
                self.logger.error(f"概述生成失败: {result['error']}")
                return False

            # 更新阶段
            status.current_phase = "assembly"
            safe_write_yaml(self.config.status_file, status)

            self.logger.info("阶段 3 完成！")
            return True
        except Exception as e:
            self.logger.error(f"概述生成失败: {e}")
            return False

    def run_assembly(self) -> bool:
        """阶段 4：组装最终文档"""
        self.logger.info("=== 阶段 4：组装 ===")

        state = self._load_existing_state()
        if not state.get("dag"):
            self.logger.error("请先运行 'init' 命令")
            return False

        graph = build_assembly_graph()
        app = graph.compile(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": "assembly"}}

        try:
            result = app.invoke(state, config)

            if result.get("error"):
                self.logger.error(f"组装失败: {result['error']}")
                return False

            self.logger.info(f"最终文档: {result.get('final_document_path')}")
            return True
        except Exception as e:
            self.logger.error(f"组装失败: {e}")
            return False

    def display_status(self) -> dict:
        """获取状态用于显示"""
        status = safe_read_yaml(self.config.status_file, ProjectStatus)
        if status is None:
            raise FileNotFoundError("状态文件不存在")

        total = len(status.modules)
        completed = sum(1 for m in status.modules if m.status == ModuleStatus.COMPLETED)
        pending = sum(1 for m in status.modules if m.status == ModuleStatus.PENDING)
        failed = sum(1 for m in status.modules if m.status == ModuleStatus.FAILED)

        return {
            "project_name": status.project_name,
            "current_phase": status.current_phase,
            "last_run": str(status.last_run) if status.last_run else "从未运行",
            "progress": {
                "total": total,
                "completed": completed,
                "pending": pending,
                "failed": failed,
                "percentage": f"{(completed / total * 100):.1f}%" if total > 0 else "0%"
            },
            "modules": [
                {"name": m.name, "status": m.status.value, "file_path": m.file_path, "error": m.error_message}
                for m in status.modules
            ]
        }
