"""LangGraph 编排器"""
from typing import Optional, Callable

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
        self._progress_callback: Optional[Callable[[dict], None]] = None
        # 使用项目路径生成唯一 thread_id，确保多用户/多项目隔离
        # 从 project_root 中提取关键部分（避免路径过长）
        # 例如: data/users/1234/projects/abc123 → docuflow-1234-abc123
        parts = config.project_root.parts
        if len(parts) >= 4 and parts[-4] == "users" and parts[-2] == "projects":
            # API 模式: data/users/{user_id}/projects/{project_id}
            user_id = parts[-3]
            project_id = parts[-1]
            self.thread_id = f"docuflow-{user_id}-{project_id}"
        else:
            # CLI 模式: 使用项目名称
            self.thread_id = f"docuflow-{config.project_root.name}"

    def set_progress_callback(self, callback: Callable[[dict], None]):
        """设置进度回调函数

        Args:
            callback: 回调函数，接收一个 dict 参数，包含:
                - type: 事件类型 (phase_change, module_start, module_complete, error, etc.)
                - data: 事件数据
        """
        self._progress_callback = callback

    def _emit_progress(self, event_type: str, data: dict):
        """发送进度事件"""
        if self._progress_callback:
            self._progress_callback({
                "type": event_type,
                "data": data
            })

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
        """加载现有状态，优先从 checkpointer 恢复"""
        # 尝试从 MemorySaver 获取最新状态（用于 full 流程的阶段间传递）
        try:
            if hasattr(self.checkpointer, 'storage') and self.checkpointer.storage:
                # MemorySaver.storage 是 dict[(thread_id, checkpoint_ns), checkpoint]
                for (tid, _), checkpoint in self.checkpointer.storage.items():
                    if tid == self.thread_id:
                        # 尝试获取状态值
                        values = checkpoint.get("channel_values") or checkpoint.get("values")
                        if values:
                            # 检查是否包含关键字段（说明是完整的 Phase 1 状态）
                            if values.get("full_document") and values.get("chunks"):
                                self.logger.info(f"✅ 从 checkpointer 恢复状态 (thread_id={self.thread_id})")
                                self.logger.debug(f"   - full_document: {len(values['full_document'])} 字符")
                                self.logger.debug(f"   - chunks: {len(values['chunks'])} 个")
                                return values
        except Exception as e:
            self.logger.warning(f"无法从 checkpointer 恢复状态: {e}")

        # 回退到文件加载（用于分阶段执行）
        self.logger.info("从文件恢复状态")
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
        self._emit_progress("phase_change", {"phase": "init", "message": "正在初始化..."})

        graph = build_init_graph()
        app = graph.compile(checkpointer=self.checkpointer)

        initial_state = self._build_initial_state()
        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            result = app.invoke(initial_state, config)

            if result.get("error"):
                self.logger.error(f"初始化失败: {result['error']}")
                self._emit_progress("error", {"phase": "init", "message": str(result['error'])})
                return False

            # 发送模块总数
            if result.get("dag"):
                dag_data = result["dag"]
                module_count = len(dag_data.get("modules", []))
                self._emit_progress("total_modules", {"count": module_count})

            self.logger.info("阶段 1 完成！")
            self._emit_progress("phase_complete", {"phase": "init", "message": "初始化完成"})
            return True
        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            self._emit_progress("error", {"phase": "init", "message": str(e)})
            return False

    def run_generation(self, step_by_step: Optional[bool] = None) -> bool:
        """阶段 2：并行拓扑生成

        使用 LangGraph Send API 实现并行处理:
        - 同时处理所有依赖已满足的模块
        - 批次完成后自动查找下一批可处理模块
        - 循环直到所有模块完成
        """
        self.logger.info("=== 阶段 2：并行拓扑生成 ===")
        self._emit_progress("phase_change", {"phase": "generation", "message": "正在生成模块设计..."})

        state = self._load_existing_state()
        if not state.get("dag"):
            self.logger.error("请先运行 'init' 命令")
            self._emit_progress("error", {"phase": "generation", "message": "请先运行 init 命令"})
            return False

        state["step_by_step_mode"] = step_by_step or False
        state["completed_modules_batch"] = []  # 初始化并行结果收集器

        graph = build_generation_graph()
        app = graph.compile(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            # 使用 stream 模式来获取中间状态，便于发送批判事件
            last_result = None
            for event in app.stream(state, config, stream_mode="values"):
                last_result = event
                # 检查是否有完成的模块批次
                completed_batch = event.get("completed_modules_batch", [])
                if completed_batch:
                    for module_result in completed_batch:
                        module_name = module_result.get("current_module")
                        if not module_name:
                            continue

                        # 发送模块开始事件
                        self._emit_progress("module_start", {"module": module_name})

                        # 发送批判相关事件
                        critique_history = module_result.get("critique_history", [])
                        for critique in critique_history:
                            self._emit_progress("critique_result", {
                                "module": module_name,
                                "iteration": critique.get("iteration"),
                                "score": critique.get("score"),
                                "passed": critique.get("passed")
                            })
                            if not critique.get("passed") and critique.get("iteration") < len(critique_history):
                                self._emit_progress("regenerate_start", {
                                    "module": module_name,
                                    "iteration": critique.get("iteration")
                                })

                        # 发送模块完成事件
                        if module_result.get("error"):
                            self._emit_progress("module_error", {
                                "module": module_name,
                                "error": module_result.get("error")
                            })
                        else:
                            self._emit_progress("module_complete", {
                                "module": module_name,
                                "critique_iterations": module_result.get("critique_iterations", 0),
                                "critique_score": module_result.get("final_score"),
                                "critique_passed": module_result.get("critique_passed", True)
                            })

            result = last_result or {}

            if result.get("error") and result.get("error_type") == "permanent":
                self.logger.error(f"生成失败: {result['error']}")
                self._emit_progress("error", {"phase": "generation", "message": str(result['error'])})
                return False

            # 重新加载状态检查完成情况
            status = safe_read_yaml(self.config.status_file, ProjectStatus)
            completed = sum(1 for m in status.modules if m.status == ModuleStatus.COMPLETED)
            failed = sum(1 for m in status.modules if m.status == ModuleStatus.FAILED)
            total = len(status.modules)

            self.logger.info(f"模块处理完成: {completed}/{total} 成功, {failed} 失败")
            self._emit_progress("phase_complete", {
                "phase": "generation",
                "message": f"模块处理完成: {completed}/{total} 成功, {failed} 失败",
                "completed": completed,
                "failed": failed,
                "total": total
            })

            # 更新阶段
            status.current_phase = "overview"
            safe_write_yaml(self.config.status_file, status)

            return True

        except Exception as e:
            self.logger.error(f"生成失败: {e}")
            self._emit_progress("error", {"phase": "generation", "message": str(e)})
            return False

    def run_overview(self) -> bool:
        """阶段 3：生成系统概述"""
        self.logger.info("=== 阶段 3：系统概述生成 ===")
        self._emit_progress("phase_change", {"phase": "overview", "message": "正在生成系统概述..."})

        state = self._load_existing_state()
        if not state.get("dag"):
            self.logger.error("请先运行 'init' 命令")
            self._emit_progress("error", {"phase": "overview", "message": "请先运行 init 命令"})
            return False

        # 检查是否有待处理模块
        status = ProjectStatus.model_validate(state["status"])
        pending_count = sum(1 for m in status.modules if m.status == ModuleStatus.PENDING)
        if pending_count > 0:
            self.logger.error("还有模块待处理，请先运行 'run' 命令")
            self._emit_progress("error", {"phase": "overview", "message": "还有模块待处理"})
            return False

        graph = build_overview_graph()
        app = graph.compile(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            result = app.invoke(state, config)

            if result.get("error") and result.get("error_type") == "permanent":
                self.logger.error(f"概述生成失败: {result['error']}")
                self._emit_progress("error", {"phase": "overview", "message": str(result['error'])})
                return False

            # 更新阶段
            status.current_phase = "assembly"
            safe_write_yaml(self.config.status_file, status)

            self.logger.info("阶段 3 完成！")
            self._emit_progress("phase_complete", {"phase": "overview", "message": "系统概述生成完成"})
            return True
        except Exception as e:
            self.logger.error(f"概述生成失败: {e}")
            self._emit_progress("error", {"phase": "overview", "message": str(e)})
            return False

    def run_assembly(self) -> bool:
        """阶段 4：组装最终文档"""
        self.logger.info("=== 阶段 4：组装 ===")
        self._emit_progress("phase_change", {"phase": "assembly", "message": "正在组装最终文档..."})

        state = self._load_existing_state()
        if not state.get("dag"):
            self.logger.error("请先运行 'init' 命令")
            self._emit_progress("error", {"phase": "assembly", "message": "请先运行 init 命令"})
            return False

        graph = build_assembly_graph()
        app = graph.compile(checkpointer=self.checkpointer)
        config = {"configurable": {"thread_id": self.thread_id}}

        try:
            result = app.invoke(state, config)

            if result.get("error"):
                self.logger.error(f"组装失败: {result['error']}")
                self._emit_progress("error", {"phase": "assembly", "message": str(result['error'])})
                return False

            final_path = result.get('final_document_path')
            self.logger.info(f"最终文档: {final_path}")
            self._emit_progress("phase_complete", {
                "phase": "assembly",
                "message": "文档组装完成",
                "output_path": final_path
            })
            return True
        except Exception as e:
            self.logger.error(f"组装失败: {e}")
            self._emit_progress("error", {"phase": "assembly", "message": str(e)})
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
