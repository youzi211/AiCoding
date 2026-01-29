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


class CritiqueLogEntry(BaseModel):
    """单次批判记录"""
    iteration: int
    timestamp: datetime = Field(default_factory=datetime.now)
    module_name: str
    score: float
    passed: bool
    suggestions: Optional[str] = None
    issues: list[str] = Field(default_factory=list)
    design_content: Optional[str] = None  # 本次批判的设计内容

    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"## 批判迭代 #{self.iteration} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"**模块**: {self.module_name}\n",
            f"**分数**: {self.score:.2f} / 1.0\n",
            f"**结果**: {'✅ 通过' if self.passed else '❌ 未通过'}\n",
        ]
        if self.issues:
            lines.append(f"\n### 发现的问题\n")
            for issue in self.issues:
                lines.append(f"- {issue}")
            lines.append("")
        if self.suggestions:
            lines.append(f"\n### 改进建议\n{self.suggestions}\n")
        lines.append("---\n")
        return "\n".join(lines)


class LLMContext(BaseModel):
    """LLM生成的上下文"""
    glossary_content: str = ""
    upstream_modules: dict[str, str] = Field(default_factory=dict)
    relevant_chunks: list[str] = Field(default_factory=list)
    module_definition: Optional[ModuleDefinition] = None

    def to_context_string(self) -> str:
        parts = []
        if self.module_definition:
            md = self.module_definition
            deps = ", ".join(md.dependencies) if md.dependencies else "无"
            parts.append(f"=== 当前模块定义 ===\n模块名: {md.name}\n描述: {md.description or '无'}\n依赖: {deps}")
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


class ModuleSummaryResponse(BaseModel):
    """模块摘要响应（用于结构化输出）"""
    module_name: str = Field(..., description="模块名称")
    purpose: str = Field(..., description="模块功能描述")
    interfaces: list[dict] = Field(default_factory=list, description="接口列表")
    database_tables: list[dict] = Field(default_factory=list, description="数据库表列表")
    dependencies: list[str] = Field(default_factory=list, description="依赖的其他模块")
    key_features: list[str] = Field(default_factory=list, description="关键功能列表")


class CritiqueResult(BaseModel):
    """批判评估结果（用于结构化输出）"""
    passed: bool = Field(..., description="是否通过评估")
    score: float = Field(..., ge=0, le=1, description="评分 0-1")
    issues: list[str] = Field(default_factory=list, description="发现的问题列表")
    suggestions: Optional[str] = Field(None, description="改进建议")


class AppConfig(BaseModel):
    """应用配置"""
    project_root: Path = Field(default=Path("."))
    input_dir: Path = Field(default=Path("input"))
    workspace_dir: Path = Field(default=Path("workspace"))
    output_dir: Path = Field(default=Path("output"))

    # LLM配置 (仅Azure)
    # 注意: model_name 仅用于记录，实际 LLM 调用使用环境变量 DOCUFLOW_MODEL_NAME
    model_name: str = Field(default="gpt-5.2")  # DEPRECATED: 仅用于记录/显示
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

    # LLM 并发控制
    llm_timeout: int = Field(default=120)  # LLM请求超时秒数
    llm_max_concurrent: int = Field(default=3)  # 最大并发LLM请求数
    llm_max_retries_sdk: int = Field(default=3)  # OpenAI SDK内部重试次数

    # 图片提取配置
    extract_images: bool = Field(default=False)  # 是否提取文档中的图片
    vision_model: Optional[str] = Field(default=None)  # 用于生成图片描述的视觉模型
    vision_max_tokens: int = Field(default=2000)  # 图片描述的最大 token 数
    vision_cache_enabled: bool = Field(default=True)  # 是否启用图片描述缓存

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

    @property
    def parsed_document_file(self) -> Path:
        """解析后的完整文档缓存"""
        return self.global_dir / "parsed_document.txt"

    @property
    def chunks_file(self) -> Path:
        """文档分块缓存"""
        return self.global_dir / "chunks.json"

    @property
    def critique_logs_dir(self) -> Path:
        """批判日志目录"""
        return self.workspace_dir / "04_critique_logs"

    @property
    def image_cache_dir(self) -> Path:
        """图片描述缓存目录（位于项目工作空间下）"""
        return self.workspace_dir / "image_descriptions"
