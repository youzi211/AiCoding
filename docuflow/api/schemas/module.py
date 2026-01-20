"""模块相关 Schema"""

from typing import Optional

from pydantic import BaseModel


class CritiqueInfo(BaseModel):
    """批判信息"""
    score: Optional[float] = None           # 批判评分 (0-1)
    passed: Optional[bool] = None           # 是否通过
    iterations: int = 0                     # 迭代次数
    suggestions: Optional[str] = None       # 最后一次的改进建议


class ModuleResponse(BaseModel):
    """模块响应"""
    name: str
    status: str
    content: Optional[str] = None
    file_path: Optional[str] = None
    dependencies: list[str] = []
    critique: Optional[CritiqueInfo] = None  # 批判信息（可选）


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
