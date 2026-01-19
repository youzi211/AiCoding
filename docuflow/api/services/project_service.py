"""项目管理服务"""

import json
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile

from docuflow.api.schemas.project import (
    ProjectMetadata,
    ProjectResponse,
    ProjectStatusResponse,
    ProgressInfo,
    ModuleStatusInfo,
)
from docuflow.api.schemas.module import (
    ModuleResponse,
    ModuleListResponse,
    GlossaryResponse,
    DAGResponse,
)
from docuflow.core.models import ProjectStatus, ArchitectureDAG
from docuflow.utils import safe_read_yaml, safe_read_json, safe_read_text


class ProjectService:
    """项目管理服务"""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.projects_dir = data_dir / "projects"
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_dir(self, project_id: str) -> Path:
        return self.projects_dir / project_id

    def _get_metadata_file(self, project_id: str) -> Path:
        return self._get_project_dir(project_id) / "project.json"

    def _get_status_file(self, project_id: str) -> Path:
        return self._get_project_dir(project_id) / "workspace" / "status.yaml"

    def _get_global_dir(self, project_id: str) -> Path:
        return self._get_project_dir(project_id) / "workspace" / "01_global"

    def _get_modules_dir(self, project_id: str) -> Path:
        return self._get_project_dir(project_id) / "workspace" / "02_modules"

    async def create_project(
        self,
        name: str,
        description: Optional[str],
        model_name: str,
        files: List[UploadFile],
    ) -> ProjectResponse:
        """创建项目"""
        metadata = ProjectMetadata(
            name=name,
            description=description,
            model_name=model_name,
        )
        project_id = metadata.id
        project_dir = self._get_project_dir(project_id)
        input_dir = project_dir / "input"

        # 创建目录结构
        input_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "workspace" / "01_global").mkdir(parents=True, exist_ok=True)
        (project_dir / "workspace" / "02_modules").mkdir(parents=True, exist_ok=True)
        (project_dir / "output").mkdir(parents=True, exist_ok=True)

        # 保存上传的文件
        for file in files:
            file_path = input_dir / file.filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

        # 保存元数据
        metadata_file = self._get_metadata_file(project_id)
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

        return ProjectResponse(
            id=metadata.id,
            name=metadata.name,
            description=metadata.description,
            model_name=metadata.model_name,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            tags=metadata.tags,
            has_status=False,
        )

    async def list_projects(self) -> List[ProjectResponse]:
        """获取项目列表"""
        projects = []
        if not self.projects_dir.exists():
            return projects

        for project_dir in self.projects_dir.iterdir():
            if project_dir.is_dir():
                project = await self.get_project(project_dir.name)
                if project:
                    projects.append(project)

        return sorted(projects, key=lambda p: p.created_at, reverse=True)

    async def get_project(self, project_id: str) -> Optional[ProjectResponse]:
        """获取项目详情"""
        metadata_file = self._get_metadata_file(project_id)
        if not metadata_file.exists():
            return None

        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = ProjectMetadata.model_validate(data)
        has_status = self._get_status_file(project_id).exists()

        return ProjectResponse(
            id=metadata.id,
            name=metadata.name,
            description=metadata.description,
            model_name=metadata.model_name,
            created_at=metadata.created_at,
            updated_at=metadata.updated_at,
            tags=metadata.tags,
            has_status=has_status,
        )

    async def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        project_dir = self._get_project_dir(project_id)
        if not project_dir.exists():
            return False

        shutil.rmtree(project_dir)
        return True

    async def get_project_status(self, project_id: str) -> Optional[ProjectStatusResponse]:
        """获取项目工作流状态"""
        status_file = self._get_status_file(project_id)

        if not status_file.exists():
            return None

        status = safe_read_yaml(status_file, ProjectStatus)
        if not status:
            return None

        # 计算进度
        total = len(status.modules)
        completed = sum(1 for m in status.modules if m.status.value == "completed")
        pending = sum(1 for m in status.modules if m.status.value == "pending")
        failed = sum(1 for m in status.modules if m.status.value == "failed")
        processing = sum(1 for m in status.modules if m.status.value == "processing")

        return ProjectStatusResponse(
            project_name=status.project_name,
            current_phase=status.current_phase,
            last_run=status.last_run,
            progress=ProgressInfo(
                total=total,
                completed=completed,
                pending=pending,
                failed=failed,
                processing=processing,
                percentage=f"{(completed / total * 100):.1f}%" if total > 0 else "0%",
            ),
            modules=[
                ModuleStatusInfo(
                    name=m.name,
                    status=m.status.value,
                    file_path=m.file_path,
                    error=m.error_message,
                )
                for m in status.modules
            ],
        )

    async def get_modules(self, project_id: str) -> Optional[ModuleListResponse]:
        """获取模块列表"""
        status = await self.get_project_status(project_id)
        if not status:
            return None

        dag_file = self._get_global_dir(project_id) / "architecture_dag.json"
        dag = safe_read_json(dag_file, ArchitectureDAG)

        # 构建依赖映射
        dep_map = {}
        if dag:
            for module in dag.modules:
                dep_map[module.name] = module.dependencies

        modules = []
        for m in status.modules:
            modules.append(
                ModuleResponse(
                    name=m.name,
                    status=m.status,
                    file_path=m.file_path,
                    dependencies=dep_map.get(m.name, []),
                )
            )

        return ModuleListResponse(modules=modules, total=len(modules))

    async def get_module_content(self, project_id: str, module_name: str) -> Optional[ModuleResponse]:
        """获取模块内容"""
        modules_dir = self._get_modules_dir(project_id)
        module_file = modules_dir / f"module_{module_name}.md"

        if not module_file.exists():
            # 尝试查找状态
            status = await self.get_project_status(project_id)
            if status:
                for m in status.modules:
                    if m.name == module_name:
                        return ModuleResponse(
                            name=m.name,
                            status=m.status,
                            content=None,
                            file_path=m.file_path,
                        )
            return None

        content = module_file.read_text(encoding="utf-8")

        # 获取状态信息
        status = await self.get_project_status(project_id)
        module_status = "unknown"
        if status:
            for m in status.modules:
                if m.name == module_name:
                    module_status = m.status
                    break

        return ModuleResponse(
            name=module_name,
            status=module_status,
            content=content,
            file_path=str(module_file),
        )

    async def get_glossary(self, project_id: str) -> Optional[GlossaryResponse]:
        """获取术语表"""
        glossary_file = self._get_global_dir(project_id) / "glossary.md"
        if not glossary_file.exists():
            return None

        content = safe_read_text(glossary_file)
        if not content:
            return None

        return GlossaryResponse(content=content)

    async def get_dag(self, project_id: str) -> Optional[DAGResponse]:
        """获取架构 DAG"""
        dag_file = self._get_global_dir(project_id) / "architecture_dag.json"
        dag = safe_read_json(dag_file, ArchitectureDAG)
        if not dag:
            return None

        return DAGResponse(
            modules=[m.model_dump() for m in dag.modules],
            total=len(dag.modules),
        )

    async def get_output_file(self, project_id: str) -> Optional[Path]:
        """获取最终输出文件路径"""
        output_file = self._get_project_dir(project_id) / "output" / "final_design_document.md"
        if not output_file.exists():
            return None
        return output_file

    def get_input_dir(self, project_id: str) -> Path:
        """获取输入目录"""
        return self._get_project_dir(project_id) / "input"

    def get_workspace_dir(self, project_id: str) -> Path:
        """获取工作空间目录"""
        return self._get_project_dir(project_id) / "workspace"

    def get_output_dir(self, project_id: str) -> Path:
        """获取输出目录"""
        return self._get_project_dir(project_id) / "output"
