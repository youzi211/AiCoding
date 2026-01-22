"""项目相关 Schema"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ProjectMetadata(BaseModel):
    """项目元数据"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: list[str] = Field(default_factory=list)


class ProjectCreateRequest(BaseModel):
    """创建项目请求（用于文档，实际使用 Form）"""
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    tags: list[str] = Field(default_factory=list)
    has_status: bool = False  # 是否已初始化


class ProgressInfo(BaseModel):
    """进度信息"""
    total: int
    completed: int
    pending: int
    failed: int
    processing: int = 0
    percentage: str


class ModuleStatusInfo(BaseModel):
    """模块状态信息"""
    name: str
    status: str
    file_path: Optional[str] = None
    error: Optional[str] = None


class ProjectStatusResponse(BaseModel):
    """项目状态响应"""
    project_name: str
    current_phase: str
    last_run: Optional[datetime] = None
    progress: ProgressInfo
    modules: list[ModuleStatusInfo]
