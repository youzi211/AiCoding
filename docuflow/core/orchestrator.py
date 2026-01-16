"""
核心工作流调度器

管理整个文档处理流水线。
"""
import json
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Optional

import networkx as nx

from docuflow.core.models import (
    AppConfig, ArchitectureDAG, ProjectStatus, ModuleProgress,
    ModuleStatus, LLMContext
)
from docuflow.parsers import DocumentParserFactory, DocumentChunker, ChunkRetriever
from docuflow.llm import (
    LLMGenerationError,
    GlossaryGenerator, DAGGenerator, ModuleDesignGenerator,
    ModuleSummaryGenerator, SystemDesignGenerator
)
from docuflow.utils import (
    get_logger, ensure_directory_structure, get_input_files,
    safe_read_text, safe_write_text, safe_read_yaml, safe_write_yaml,
    safe_read_json, safe_write_json, module_name_to_filename, get_timestamp
)


class WorkflowOrchestrator:
    """DocuFlow-AI 核心工作流调度器"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.logger = get_logger()
        self.parser_factory = DocumentParserFactory()
        self.chunker = DocumentChunker(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap
        )

        # 状态
        self._graph: Optional[nx.DiGraph] = None
        self._status: Optional[ProjectStatus] = None
        self._dag: Optional[ArchitectureDAG] = None
        self._chunks = None
        self._retriever: Optional[ChunkRetriever] = None

    # 延迟初始化生成器
    @cached_property
    def glossary_generator(self) -> GlossaryGenerator:
        return GlossaryGenerator(self.config)

    @cached_property
    def dag_generator(self) -> DAGGenerator:
        return DAGGenerator(self.config)

    @cached_property
    def module_generator(self) -> ModuleDesignGenerator:
        return ModuleDesignGenerator(self.config)

    @cached_property
    def summary_generator(self) -> ModuleSummaryGenerator:
        return ModuleSummaryGenerator(self.config)

    @cached_property
    def system_design_generator(self) -> SystemDesignGenerator:
        return SystemDesignGenerator(self.config)

    # ============================================================
    # 文档加载
    # ============================================================

    def _load_and_parse_documents(self) -> tuple[str, list]:
        """加载并解析所有输入文档"""
        input_files = get_input_files(self.config.input_dir)
        if not input_files:
            raise FileNotFoundError(f"在 {self.config.input_dir} 中未找到输入文档")

        self.logger.info(f"找到 {len(input_files)} 个输入文档")

        combined_content = []
        for file_path in input_files:
            self.logger.info(f"正在解析: {file_path.name}")
            content = self.parser_factory.parse(file_path)
            combined_content.append(content)

        full_document = "\n\n---\n\n".join(combined_content)
        chunks = self.chunker.chunk_with_metadata(full_document, "requirements")

        return full_document, chunks

    def _ensure_retriever(self) -> None:
        """确保检索器已初始化"""
        if self._retriever is not None:
            return
        try:
            _, chunks = self._load_and_parse_documents()
            self._chunks = chunks
            self._retriever = ChunkRetriever(chunks, method=self.config.retrieval_method)
        except FileNotFoundError:
            self.logger.warning("无输入文档，检索器未初始化")

    # ============================================================
    # 图操作
    # ============================================================

    def load_graph(self) -> nx.DiGraph:
        """加载架构 DAG"""
        self.logger.info("正在加载架构 DAG...")
        dag = safe_read_json(self.config.dag_file, ArchitectureDAG)
        if dag is None:
            raise FileNotFoundError(f"架构 DAG 不存在: {self.config.dag_file}")

        self._dag = dag
        G = nx.DiGraph()

        for module in dag.modules:
            G.add_node(module.name, definition=module)
            for dep in module.dependencies:
                G.add_edge(dep, module.name)

        if not nx.is_directed_acyclic_graph(G):
            raise ValueError(f"架构图包含循环: {list(nx.simple_cycles(G))}")

        self._graph = G
        self.logger.info(f"已加载 {G.number_of_nodes()} 个模块")
        return G

    def get_topological_order(self) -> list[str]:
        """获取拓扑排序"""
        if self._graph is None:
            self.load_graph()
        return list(nx.topological_sort(self._graph))

    # ============================================================
    # 状态管理
    # ============================================================

    def load_status(self) -> ProjectStatus:
        """加载项目状态"""
        status = safe_read_yaml(self.config.status_file, ProjectStatus)
        if status is None:
            status = ProjectStatus()
        self._status = status
        return status

    def save_status(self) -> bool:
        """保存项目状态"""
        if self._status is None:
            return False
        self._status.last_run = datetime.now()
        return safe_write_yaml(self.config.status_file, self._status)

    def initialize_status_from_dag(self) -> None:
        """从 DAG 初始化状态"""
        if self._dag is None:
            self.load_graph()
        if self._status is None:
            self._status = ProjectStatus()

        existing_names = {m.name for m in self._status.modules}
        for module_def in self._dag.modules:
            if module_def.name not in existing_names:
                self._status.modules.append(ModuleProgress(
                    name=module_def.name,
                    status=ModuleStatus.PENDING,
                    dependencies=module_def.dependencies
                ))
        self.save_status()

    def get_module_count(self, status: ModuleStatus) -> int:
        """获取指定状态的模块数量"""
        if self._status is None:
            self.load_status()
        return sum(1 for m in self._status.modules if m.status == status)

    # ============================================================
    # 任务调度
    # ============================================================

    def get_next_task(self) -> Optional[str]:
        """获取下一个待处理模块"""
        if self._status is None:
            self.load_status()
        if self._graph is None:
            self.load_graph()

        topo_order = self.get_topological_order()
        status_lookup = {m.name: m.status for m in self._status.modules}

        for module_name in topo_order:
            if status_lookup.get(module_name) != ModuleStatus.PENDING:
                continue

            module_def = self._dag.get_module(module_name)
            if module_def and all(
                status_lookup.get(dep) == ModuleStatus.COMPLETED
                for dep in module_def.dependencies
            ):
                return module_name

        return None

    # ============================================================
    # 上下文组装
    # ============================================================

    def build_context(self, module_name: str) -> LLMContext:
        """为模块构建 LLM 上下文"""
        context = LLMContext()
        context.glossary_content = safe_read_text(self.config.glossary_file)

        if self._dag is None:
            self.load_graph()

        module_def = self._dag.get_module(module_name)
        if module_def:
            context.module_definition = module_def
            for dep_name in module_def.dependencies:
                dep_file = self.config.modules_dir / module_name_to_filename(dep_name)
                dep_content = safe_read_text(dep_file)
                if dep_content:
                    context.upstream_modules[dep_name] = dep_content

        if self._retriever is not None:
            query = f"{module_name} {module_def.description or ''}"
            context.relevant_chunks = self._retriever.retrieve(query, top_k=self.config.top_k_chunks)

        return context

    # ============================================================
    # 阶段 1：初始化
    # ============================================================

    def run_init(self) -> bool:
        """阶段 1：初始化"""
        self.logger.info("=== 阶段 1：初始化 ===")

        if not ensure_directory_structure(self.config):  # 传入 config 而不是 project_root
            return False

        try:
            full_document, chunks = self._load_and_parse_documents()
            self._chunks = chunks
            self._retriever = ChunkRetriever(chunks, method=self.config.retrieval_method)
        except FileNotFoundError as e:
            self.logger.error(str(e))
            return False

        try:
            self.logger.info("正在生成术语表...")
            glossary = self.glossary_generator.generate(full_document)
            safe_write_text(self.config.glossary_file, glossary.to_markdown())

            self.logger.info("正在生成架构 DAG...")
            dag = self.dag_generator.generate(full_document, glossary.to_markdown())
            safe_write_json(self.config.dag_file, dag)
            self._dag = dag

            self.load_status()
            self._status.current_phase = "generation"
            self.initialize_status_from_dag()

            self.logger.info("阶段 1 完成！")
            return True
        except LLMGenerationError as e:
            self.logger.error(f"LLM 生成失败: {e}")
            return False

    # ============================================================
    # 阶段 2：拓扑生成
    # ============================================================

    def run_generation(self, step_by_step: Optional[bool] = None) -> bool:
        """阶段 2：拓扑生成"""
        self.logger.info("=== 阶段 2：拓扑生成 ===")

        step_mode = step_by_step if step_by_step is not None else self.config.step_by_step_mode
        self.load_graph()
        self.load_status()
        self._ensure_retriever()

        while True:
            next_module = self.get_next_task()
            if next_module is None:
                self.logger.info("所有模块已完成！")
                self._status.current_phase = "overview"
                self.save_status()
                return True

            success = self._process_module(next_module)
            if not success:
                return False
            if step_mode:
                self.logger.info(f"逐步模式：'{next_module}' 后暂停")
                return True

    def _process_module(self, module_name: str) -> bool:
        """处理单个模块"""
        self.logger.info(f"正在处理模块: {module_name}")
        self._status.update_module_status(module_name, ModuleStatus.PROCESSING)
        self.save_status()

        try:
            context = self.build_context(module_name)
            design_content = self.module_generator.generate(module_name, context)

            header = f"# 模块设计: {module_name}\n\n生成时间: {get_timestamp()}\n\n---\n\n"
            output_file = self.config.modules_dir / module_name_to_filename(module_name)
            safe_write_text(output_file, header + design_content)

            self._status.update_module_status(
                module_name, ModuleStatus.COMPLETED,
                file_path=str(output_file.relative_to(self.config.project_root))
            )
            self.save_status()
            self.logger.info(f"模块 '{module_name}' 完成")
            return True
        except LLMGenerationError as e:
            self.logger.error(f"模块 '{module_name}' 生成失败: {e}")
            self._status.update_module_status(module_name, ModuleStatus.FAILED, error_message=str(e))
            self.save_status()
            return False

    # ============================================================
    # 阶段 3：系统概述
    # ============================================================

    def run_overview(self) -> bool:
        """阶段 3：生成系统级设计"""
        self.logger.info("=== 阶段 3：系统概述生成 ===")

        self.load_graph()
        self.load_status()

        if self.get_module_count(ModuleStatus.PENDING) > 0:
            self.logger.error("还有模块待处理，请先运行 'run' 命令")
            return False

        try:
            self.logger.info("正在提取模块摘要...")
            summaries = []
            for module_name in self.get_topological_order():
                module_file = self.config.modules_dir / module_name_to_filename(module_name)
                content = safe_read_text(module_file)
                if content:
                    summary = self.summary_generator.generate(module_name, content)
                    summaries.append(summary)

            summaries_text = self._format_summaries(summaries)

            self.logger.info("正在生成系统设计...")
            safe_write_text(
                self.config.global_dir / "system_design.md",
                self.system_design_generator.generate_system_design(summaries_text)
            )

            self.logger.info("正在生成接口设计...")
            safe_write_text(
                self.config.global_dir / "interface_design.md",
                self.system_design_generator.generate_interface_design(summaries_text)
            )

            self.logger.info("正在生成数据库设计...")
            safe_write_text(
                self.config.global_dir / "database_design.md",
                self.system_design_generator.generate_database_design(summaries_text)
            )

            safe_write_text(
                self.config.global_dir / "module_summaries.json",
                json.dumps(summaries, ensure_ascii=False, indent=2)
            )

            self._status.current_phase = "assembly"
            self.save_status()
            self.logger.info("阶段 3 完成！")
            return True
        except LLMGenerationError as e:
            self.logger.error(f"LLM 生成失败: {e}")
            return False

    def _format_summaries(self, summaries: list[dict]) -> str:
        """格式化摘要列表"""
        lines = []
        for s in summaries:
            lines.append(f"### 模块: {s.get('module_name', '未知')}")
            lines.append(f"职责: {s.get('purpose', '无')}")

            for api in s.get('interfaces', [])[:5]:
                lines.append(f"  - {api.get('method', 'GET')} {api.get('path', '/')} - {api.get('description', '')}")

            for t in s.get('database_tables', [])[:5]:
                lines.append(f"  - 表: {t.get('name', '')} - {t.get('description', '')}")

            if deps := s.get('dependencies', []):
                lines.append(f"依赖: {', '.join(deps)}")

            lines.append("")
        return "\n".join(lines)

    # ============================================================
    # 阶段 4：组装
    # ============================================================

    def run_assembly(self) -> bool:
        """阶段 4：组装最终文档"""
        self.logger.info("=== 阶段 4：组装 ===")

        self.load_graph()
        self.load_status()
        topo_order = self.get_topological_order()

        sections = [
            f"# {self._status.project_name} - 软件设计文档\n",
            f"生成时间: {get_timestamp()}\n",
            "\n## 目录\n",
            "1. [概述说明](#1-概述说明)\n   - 1.1 [术语与缩略词](#11-术语与缩略词)\n",
            "2. [系统设计](#2-系统设计)\n",
            "3. [模块设计](#3-模块设计)\n",
        ]

        for i, name in enumerate(topo_order, 1):
            sections.append(f"   - 3.{i} [{name}](#3{i}-{name.replace(' ', '-')})\n")

        sections.append("4. [接口设计](#4-接口设计)\n5. [数据库设计](#5-数据库设计)\n")

        # 1. 概述
        sections.append("\n---\n# 1 概述说明\n\n## 1.1 术语与缩略词\n")
        glossary = safe_read_text(self.config.glossary_file)
        for line in glossary.split('\n'):
            if not line.startswith('# '):
                sections.append(line + "\n")

        # 2. 系统设计
        sections.append("\n---\n# 2 系统设计\n")
        sections.append(safe_read_text(self.config.global_dir / "system_design.md") or "*待生成*\n")

        # 3. 模块设计
        sections.append("\n---\n# 3 模块设计\n")
        for i, name in enumerate(topo_order, 1):
            sections.append(f"\n## 3.{i} {name}\n")
            content = safe_read_text(self.config.modules_dir / module_name_to_filename(name))
            for line in content.split('\n'):
                if not (line.startswith('# 模块设计:') or line.startswith('生成时间:') or line == '---'):
                    sections.append(line + "\n")

        # 4. 接口设计
        sections.append("\n---\n# 4 接口设计\n")
        sections.append(safe_read_text(self.config.global_dir / "interface_design.md") or "*待生成*\n")

        # 5. 数据库设计
        sections.append("\n---\n# 5 数据库设计\n")
        sections.append(safe_read_text(self.config.global_dir / "database_design.md") or "*待生成*\n")

        output_file = self.config.output_dir / "final_design_document.md"
        if not safe_write_text(output_file, "".join(sections)):
            return False

        self._status.current_phase = "completed"
        self.save_status()
        self.logger.info(f"最终文档: {output_file}")
        return True

    # ============================================================
    # 状态显示
    # ============================================================

    def display_status(self) -> dict:
        """获取状态用于显示"""
        self.load_status()

        total = len(self._status.modules)
        completed = self.get_module_count(ModuleStatus.COMPLETED)
        pending = self.get_module_count(ModuleStatus.PENDING)
        failed = self.get_module_count(ModuleStatus.FAILED)

        return {
            "project_name": self._status.project_name,
            "current_phase": self._status.current_phase,
            "last_run": str(self._status.last_run) if self._status.last_run else "从未运行",
            "progress": {
                "total": total,
                "completed": completed,
                "pending": pending,
                "failed": failed,
                "percentage": f"{(completed / total * 100):.1f}%" if total > 0 else "0%"
            },
            "modules": [
                {"name": m.name, "status": m.status.value, "file_path": m.file_path, "error": m.error_message}
                for m in self._status.modules
            ]
        }
