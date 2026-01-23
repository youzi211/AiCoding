"""任务执行服务"""

import asyncio
import contextvars
import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Callable

from docuflow.api.schemas.task import Task, TaskStatus, TaskType, TaskProgress
from docuflow.api.services.notification_service import NotificationService
from docuflow.api.services.project_service import ProjectService
from docuflow.core.config import create_app_config
from docuflow.core.models import AppConfig
from docuflow.graph.orchestrator import WorkflowOrchestrator
from docuflow.utils import get_logger
from docuflow.utils.logging import set_task_context


class TaskManager:
    """任务管理器 - 管理后台工作流任务"""

    def __init__(
        self,
        project_service: ProjectService,
        notification_service: NotificationService,
        max_workers: int = 4,
    ):
        self.project_service = project_service
        self.notification_service = notification_service
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tasks: Dict[str, Task] = {}
        self.cancel_flags: Dict[str, bool] = {}
        self.lock = threading.RLock()  # 可重入锁，保护并发访问
        self.logger = get_logger()

    def _create_app_config(self, user_id: str, project_id: str, model_name: str) -> AppConfig:
        """为项目创建 AppConfig"""
        from docuflow.core.config import get_settings

        project_dir = self.project_service._get_project_dir(user_id, project_id)
        settings = get_settings()

        return AppConfig(
            project_root=project_dir,
            input_dir=project_dir / "input",
            workspace_dir=project_dir / "workspace",
            output_dir=project_dir / "output",
            model_name=model_name,
            # 从环境变量读取的配置
            llm_temperature=settings.llm_temperature,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            max_retries=settings.max_retries,
            step_by_step_mode=settings.step_by_step,
            retrieval_method=settings.retrieval_method,
            top_k_chunks=settings.top_k_chunks,
            critique_enabled=settings.critique_enabled,
            critique_threshold=settings.critique_threshold,
            critique_max_iterations=settings.critique_max_iterations,
            critique_model=settings.critique_model,
            llm_timeout=settings.llm_timeout,
            llm_max_concurrent=settings.llm_max_concurrent,
            llm_max_retries_sdk=settings.llm_max_retries_sdk,
            extract_images=settings.extract_images,
            vision_model=settings.vision_model,
            vision_max_tokens=settings.vision_max_tokens,
            vision_cache_enabled=settings.vision_cache_enabled,
        )

    async def submit_task(
        self,
        user_id: str,
        project_id: str,
        task_type: TaskType,
        model_name: str,
        step_by_step: bool = False,
    ) -> Task:
        """提交后台任务（线程安全）"""
        task = Task(
            project_id=project_id,
            user_id=user_id,  # 直接在构造函数中传入
            task_type=task_type,
        )

        with self.lock:  # 加锁保护字典操作
            self.tasks[task.id] = task
            self.cancel_flags[task.id] = False

        # 复制当前上下文并提交到线程池执行（确保上下文传播）
        loop = asyncio.get_event_loop()
        ctx = contextvars.copy_context()
        loop.run_in_executor(
            self.executor,
            ctx.run,
            self._run_task,
            task,
            model_name,
            step_by_step,
            loop,
        )

        return task

    def _run_task(
        self,
        task: Task,
        model_name: str,
        step_by_step: bool,
        loop: asyncio.AbstractEventLoop,
    ):
        """在线程中执行任务"""
        # 设置任务上下文（线程安全）
        set_task_context(
            task_id=task.id,
            user_id=task.user_id,
            project_id=task.project_id
        )
        
        # 更新状态时加锁
        with self.lock:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

        try:
            config = self._create_app_config(task.user_id, task.project_id, model_name)
            orchestrator = WorkflowOrchestrator(config)

            # 设置进度回调
            def on_progress(event: dict):
                self._handle_progress(task, event, loop)

            orchestrator.set_progress_callback(on_progress)

            # 根据任务类型执行
            if task.task_type == TaskType.FULL:
                self._run_full_workflow(orchestrator, task, step_by_step)
            elif task.task_type == TaskType.INIT:
                orchestrator.run_init()
            elif task.task_type == TaskType.GENERATION:
                orchestrator.run_generation(step_by_step=step_by_step)
            elif task.task_type == TaskType.OVERVIEW:
                orchestrator.run_overview()
            elif task.task_type == TaskType.ASSEMBLY:
                orchestrator.run_assembly()

            # 完成时加锁
            with self.lock:
                if self.cancel_flags.get(task.id):
                    task.status = TaskStatus.CANCELLED
                else:
                    task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()

        except Exception as e:
            self.logger.error(f"任务执行失败: {e}")
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.now()

        finally:
            # 发送完成通知
            self._notify_complete(task, loop)

    def _run_full_workflow(
        self,
        orchestrator: WorkflowOrchestrator,
        task: Task,
        step_by_step: bool,
    ):
        """执行完整工作流"""
        # 阶段 1: 初始化
        task.progress.current_phase = "init"
        task.progress.message = "正在初始化..."
        if not orchestrator.run_init():
            raise Exception("初始化失败")

        if self.cancel_flags.get(task.id):
            return

        # 阶段 2: 模块生成
        task.progress.current_phase = "generation"
        task.progress.message = "正在生成模块设计..."
        if not orchestrator.run_generation(step_by_step=step_by_step):
            raise Exception("模块生成失败")

        if self.cancel_flags.get(task.id):
            return

        # 阶段 3: 系统概述
        task.progress.current_phase = "overview"
        task.progress.message = "正在生成系统概述..."
        if not orchestrator.run_overview():
            raise Exception("系统概述生成失败")

        if self.cancel_flags.get(task.id):
            return

        # 阶段 4: 组装
        task.progress.current_phase = "assembly"
        task.progress.message = "正在组装最终文档..."
        if not orchestrator.run_assembly():
            raise Exception("文档组装失败")

        task.progress.current_phase = "completed"
        task.progress.message = "处理完成"

    def _handle_progress(self, task: Task, event: dict, loop: asyncio.AbstractEventLoop):
        """处理进度事件（线程安全）"""
        event_type = event.get("type")
        data = event.get("data", {})

        # 更新任务进度时加锁
        with self.lock:
            if event_type == "phase_change":
                task.progress.current_phase = data.get("phase")
            elif event_type == "module_start":
                task.progress.current_module = data.get("module")
            elif event_type == "module_complete":
                task.progress.completed_modules += 1
                task.progress.current_module = None
            elif event_type == "total_modules":
                task.progress.total_modules = data.get("count", 0)
            # 批判相关事件
            elif event_type == "critique_start":
                task.progress.critique_iteration = data.get("iteration", 0)
            elif event_type == "critique_result":
                task.progress.critique_iteration = data.get("iteration", 0)
                if not data.get("passed", True):
                    task.progress.critique_total_iterations += 1
            elif event_type == "regenerate_start":
                pass  # 仅转发给前端

            task.progress.message = data.get("message", task.progress.message)

        # 广播到 WebSocket
        asyncio.run_coroutine_threadsafe(
            self.notification_service.broadcast(
                task.project_id,
                {
                    "type": event_type,
                    "timestamp": datetime.now().isoformat(),
                    "task_id": task.id,
                    "data": data,
                },
            ),
            loop,
        )

    def _notify_complete(self, task: Task, loop: asyncio.AbstractEventLoop):
        """发送任务完成通知"""
        asyncio.run_coroutine_threadsafe(
            self.notification_service.broadcast(
                task.project_id,
                {
                    "type": "task_complete",
                    "timestamp": datetime.now().isoformat(),
                    "task_id": task.id,
                    "data": {
                        "status": task.status.value,
                        "error_message": task.error_message,
                    },
                },
            ),
            loop,
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务（线程安全，返回快照）"""
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                return deepcopy(task)  # 返回深拷贝，避免并发修改
            return None

    def get_project_tasks(self, project_id: str, user_id: Optional[str] = None) -> list[Task]:
        """获取项目任务列表（线程安全，支持 user_id 过滤）"""
        with self.lock:
            tasks = [
                deepcopy(t) for t in self.tasks.values()
                if t.project_id == project_id and (user_id is None or t.user_id == user_id)
            ]
        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """取消任务（线程安全）"""
        with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]
            if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                return False

            self.cancel_flags[task_id] = True
        return True

    def shutdown(self):
        """关闭任务管理器"""
        with self.lock:
            # 取消所有运行中的任务
            for task_id in list(self.tasks.keys()):
                self.cancel_flags[task_id] = True

        # 等待线程池关闭
        self.executor.shutdown(wait=True)
