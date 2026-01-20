"""
数据模型定义

定义 DocuFlow-AI 系统使用的所有数据结构。
"""
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ModuleStatus(str, Enum):
    """模块在生成流水线中的状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ModuleDefinition(BaseModel):
    """架构DAG中的模块定义"""
    name: str = Field(..., min_length=1)
    dependencies: list[str] = Field(default_factory=list)
    description: Optional[str] = None

    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return v.strip()


class ArchitectureDAG(BaseModel):
    """架构依赖图"""
    modules: list[ModuleDefinition] = Field(..., min_length=1)
    version: str = Field(default="1.0")
    generated_at: Optional[datetime] = None

    def get_module(self, name: str) -> Optional[ModuleDefinition]:
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def get_all_module_names(self) -> list[str]:
        return [m.name for m in self.modules]


class ModuleProgress(BaseModel):
    """单个模块的进度追踪"""
    name: str
    status: ModuleStatus = ModuleStatus.PENDING
    file_path: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class ProjectStatus(BaseModel):
    """项目状态"""
    project_name: str = Field(default="DocuFlow-AI Project")
    created_at: datetime = Field(default_factory=datetime.now)
    last_run: Optional[datetime] = None
    current_phase: str = Field(default="init")
    modules: list[ModuleProgress] = Field(default_factory=list)

    def get_module_status(self, name: str) -> Optional[ModuleProgress]:
        for module in self.modules:
            if module.name == name:
                return module
        return None

    def update_module_status(
        self,
        name: str,
        status: ModuleStatus,
        file_path: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        for module in self.modules:
            if module.name == name:
                module.status = status
                if file_path:
                    module.file_path = file_path
                if status == ModuleStatus.PROCESSING:
                    module.started_at = datetime.now()
                elif status == ModuleStatus.COMPLETED:
                    module.completed_at = datetime.now()
                elif status == ModuleStatus.FAILED:
                    module.error_message = error_message
                    module.retry_count += 1
                break


class GlossaryEntry(BaseModel):
    """术语表条目"""
    term: str
    definition: str
    category: Optional[str] = None
    aliases: list[str] = Field(default_factory=list)


class Glossary(BaseModel):
    """术语表集合"""
    entries: list[GlossaryEntry] = Field(default_factory=list)

    def to_markdown(self) -> str:
        lines = ["# 术语表\n"]
        categories: dict[str, list[GlossaryEntry]] = {}

        for entry in self.entries:
            cat = entry.category or "通用"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(entry)

        for category, entries in categories.items():
            lines.append(f"\n## {category}\n")
            for entry in entries:
                aliases = f" (别名: {', '.join(entry.aliases)})" if entry.aliases else ""
                lines.append(f"- **{entry.term}**{aliases}: {entry.definition}")

        return "\n".join(lines)


class LLMContext(BaseModel):
    """LLM生成的上下文"""
    glossary_content: str = ""
    upstream_modules: dict[str, str] = Field(default_factory=dict)
    relevant_chunks: list[str] = Field(default_factory=list)
    module_definition: Optional[ModuleDefinition] = None

    def to_context_string(self) -> str:
        parts = []
        if self.glossary_content:
            parts.append("=== 全局术语表 ===\n" + self.glossary_content)
        if self.upstream_modules:
            parts.append("=== 上游模块设计 ===")
            for name, content in self.upstream_modules.items():
                parts.append(f"\n--- {name} ---\n{content}")
        if self.relevant_chunks:
            parts.append("=== 相关需求内容 ===")
            for i, chunk in enumerate(self.relevant_chunks, 1):
                parts.append(f"\n--- 片段 {i} ---\n{chunk}")
        return "\n\n".join(parts)


class AppConfig(BaseModel):
    """应用配置"""
    project_root: Path = Field(default=Path("."))
    input_dir: Path = Field(default=Path("input"))
    workspace_dir: Path = Field(default=Path("workspace"))
    output_dir: Path = Field(default=Path("output"))

    # LLM配置 (仅Azure)
    llm_temperature: float = Field(default=0.3, ge=0, le=2)

    # 处理配置
    chunk_size: int = Field(default=2000)
    chunk_overlap: int = Field(default=200)
    max_retries: int = Field(default=3)
    step_by_step_mode: bool = Field(default=False)

    # 检索配置
    retrieval_method: str = Field(default="keyword")
    top_k_chunks: int = Field(default=5)

    # 批判配置
    critique_enabled: bool = Field(default=True)
    critique_threshold: float = Field(default=0.7, ge=0, le=1)
    critique_max_iterations: int = Field(default=2, ge=1)
    critique_model: Optional[str] = Field(default=None)  # 批判使用的模型

    @property
    def global_dir(self) -> Path:
        return self.workspace_dir / "01_global"

    @property
    def modules_dir(self) -> Path:
        return self.workspace_dir / "02_modules"

    @property
    def status_file(self) -> Path:
        return self.workspace_dir / "status.yaml"

    @property
    def dag_file(self) -> Path:
        return self.global_dir / "architecture_dag.json"

    @property
    def glossary_file(self) -> Path:
        return self.global_dir / "glossary.md"
