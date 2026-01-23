"""模块内容路由"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from docuflow.api.schemas.module import (
    ModuleResponse,
    ModuleListResponse,
    GlossaryResponse,
    DAGResponse,
)
from docuflow.utils import validate_user_id

router = APIRouter()


def get_project_service(request: Request):
    """获取项目服务"""
    return request.app.state.project_service


@router.get("/users/{user_id}/projects/{project_id}/modules", response_model=ModuleListResponse)
async def list_modules(user_id: str, project_id: str, request: Request):
    """获取模块列表"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    modules = await project_service.get_modules(user_id, project_id)
    if not modules:
        raise HTTPException(status_code=404, detail="项目尚未初始化")

    return modules


@router.get("/users/{user_id}/projects/{project_id}/modules/{module_name}", response_model=ModuleResponse)
async def get_module(user_id: str, project_id: str, module_name: str, request: Request):
    """获取模块设计内容"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    module = await project_service.get_module_content(user_id, project_id, module_name)
    if not module:
        raise HTTPException(status_code=404, detail=f"模块 '{module_name}' 不存在")

    return module


@router.get("/users/{user_id}/projects/{project_id}/glossary", response_model=GlossaryResponse)
async def get_glossary(user_id: str, project_id: str, request: Request):
    """获取术语表"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    glossary = await project_service.get_glossary(user_id, project_id)
    if not glossary:
        raise HTTPException(status_code=404, detail="术语表尚未生成")

    return glossary


@router.get("/users/{user_id}/projects/{project_id}/dag", response_model=DAGResponse)
async def get_dag(user_id: str, project_id: str, request: Request):
    """获取架构 DAG"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    dag = await project_service.get_dag(user_id, project_id)
    if not dag:
        raise HTTPException(status_code=404, detail="架构 DAG 尚未生成")

    return dag


@router.get("/users/{user_id}/projects/{project_id}/output")
async def download_output(user_id: str, project_id: str, request: Request):
    """下载最终设计文档"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    output_file = await project_service.get_output_file(user_id, project_id)
    if not output_file:
        raise HTTPException(status_code=404, detail="最终文档尚未生成")

    return FileResponse(
        path=output_file,
        filename="final_design_document.md",
        media_type="text/markdown",
    )


@router.get("/users/{user_id}/projects/{project_id}/system-design")
async def get_system_design(user_id: str, project_id: str, request: Request):
    """获取系统设计文档"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    global_dir = project_service._get_global_dir(user_id, project_id)
    system_design_file = global_dir / "system_design.md"

    if not system_design_file.exists():
        raise HTTPException(status_code=404, detail="系统设计文档尚未生成")

    content = system_design_file.read_text(encoding="utf-8")
    return {"content": content}


@router.get("/users/{user_id}/projects/{project_id}/interface-design")
async def get_interface_design(user_id: str, project_id: str, request: Request):
    """获取接口设计文档"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    global_dir = project_service._get_global_dir(user_id, project_id)
    interface_design_file = global_dir / "interface_design.md"

    if not interface_design_file.exists():
        raise HTTPException(status_code=404, detail="接口设计文档尚未生成")

    content = interface_design_file.read_text(encoding="utf-8")
    return {"content": content}


@router.get("/users/{user_id}/projects/{project_id}/database-design")
async def get_database_design(user_id: str, project_id: str, request: Request):
    """获取数据库设计文档"""
    user_id = validate_user_id(user_id)
    project_service = get_project_service(request)

    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    global_dir = project_service._get_global_dir(user_id, project_id)
    database_design_file = global_dir / "database_design.md"

    if not database_design_file.exists():
        raise HTTPException(status_code=404, detail="数据库设计文档尚未生成")

    content = database_design_file.read_text(encoding="utf-8")
    return {"content": content}
