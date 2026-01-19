"""模块相关 Schema"""

from typing import Optional

from pydantic import BaseModel


class ModuleResponse(BaseModel):
    """模块响应"""
    name: str
    status: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    dependencies: list[str] = []


class ModuleListResponse(BaseModel):
    """模块列表响应"""
    modules: list[ModuleResponse]
    total: int


class GlossaryResponse(BaseModel):
    """术语表响应"""
    content: str


class DAGResponse(BaseModel):
    """架构 DAG 响应"""
    modules: list[dict]
    total: int
