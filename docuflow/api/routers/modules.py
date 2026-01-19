"""模块内容路由"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from docuflow.api.schemas.module import (
    ModuleResponse,
    ModuleListResponse,
    GlossaryResponse,
    DAGResponse,
)

router = APIRouter()


def get_project_service(request: Request):
    """获取项目服务"""
    return request.app.state.project_service


@router.get("/projects/{project_id}/modules", response_model=ModuleListResponse)
async def list_modules(project_id: str, request: Request):
    """获取模块列表"""
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    modules = await project_service.get_modules(project_id)
    if not modules:
        raise HTTPException(status_code=404, detail="项目尚未初始化")

    return modules


@router.get("/projects/{project_id}/modules/{module_name}", response_model=ModuleResponse)
async def get_module(project_id: str, module_name: str, request: Request):
    """获取模块设计内容"""
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    module = await project_service.get_module_content(project_id, module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"模块 '{module_name}' 不存在")

    return module


@router.get("/projects/{project_id}/glossary", response_model=GlossaryResponse)
async def get_glossary(project_id: str, request: Request):
    """获取术语表"""
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    glossary = await project_service.get_glossary(project_id)
    if not glossary:
        raise HTTPException(status_code=404, detail="术语表尚未生成")

    return glossary


@router.get("/projects/{project_id}/dag", response_model=DAGResponse)
async def get_dag(project_id: str, request: Request):
    """获取架构 DAG"""
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    dag = await project_service.get_dag(project_id)
    if not dag:
        raise HTTPException(status_code=404, detail="架构 DAG 尚未生成")

    return dag


@router.get("/projects/{project_id}/output")
async def download_output(project_id: str, request: Request):
    """下载最终设计文档"""
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    output_file = await project_service.get_output_file(project_id)
    if not output_file:
        raise HTTPException(status_code=404, detail="最终文档尚未生成")

    return FileResponse(
        path=output_file,
        filename="final_design_document.md",
        media_type="text/markdown",
    )


@router.get("/projects/{project_id}/system-design")
async def get_system_design(project_id: str, request: Request):
    """获取系统设计文档"""
    project_service = get_project_service(request)

    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    global_dir = project_service._get_global_dir(project_id)
    system_design_file = global_dir / "system_design.md"

    if not system_design_file.exists():
        raise HTTPException(status_code=404, detail="系统设计文档尚未生成")

    content = system_design_file.read_text(encoding="utf-8")
    return {"content": content}


@router.get("/projects/{project_id}/interface-design")
async def get_interface_design(project_id: str, request: Request):
    """获取接口设计文档"""
    project_service = get_project_service(request)

    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    global_dir = project_service._get_global_dir(project_id)
    interface_design_file = global_dir / "interface_design.md"

    if not interface_design_file.exists():
        raise HTTPException(status_code=404, detail="接口设计文档尚未生成")

    content = interface_design_file.read_text(encoding="utf-8")
    return {"content": content}


@router.get("/projects/{project_id}/database-design")
async def get_database_design(project_id: str, request: Request):
    """获取数据库设计文档"""
    project_service = get_project_service(request)

    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    global_dir = project_service._get_global_dir(project_id)
    database_design_file = global_dir / "database_design.md"

    if not database_design_file.exists():
        raise HTTPException(status_code=404, detail="数据库设计文档尚未生成")

    content = database_design_file.read_text(encoding="utf-8")
    return {"content": content}
