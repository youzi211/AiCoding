"""任务相关 Schema"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """任务类型"""
    INIT = "init"
    GENERATION = "generation"
    OVERVIEW = "overview"
    ASSEMBLY = "assembly"
    FULL = "full"


class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    task_type: TaskType = TaskType.FULL
    step_by_step: bool = False


class TaskProgress(BaseModel):
    """任务进度"""
    current_phase: Optional[str] = None
    current_module: Optional[str] = None
    completed_modules: int = 0
    total_modules: int = 0
    message: Optional[str] = None
    # 批判相关进度
    critique_iteration: int = 0              # 当前模块批判迭代次数
    critique_total_iterations: int = 0       # 所有模块批判总迭代次数


class TaskResponse(BaseModel):
    """任务响应"""
    id: str
    project_id: str
    user_id: str
    task_type: TaskType
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: TaskProgress = Field(default_factory=TaskProgress)


class Task(BaseModel):
    """内部任务模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    project_id: str
    user_id: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress: TaskProgress = Field(default_factory=TaskProgress)

    def to_response(self) -> TaskResponse:
        """转换为响应模型"""
        return TaskResponse(
            id=self.id,
            project_id=self.project_id,
            user_id=self.user_id,
            task_type=self.task_type,
            status=self.status,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            error_message=self.error_message,
            progress=self.progress,
        )
