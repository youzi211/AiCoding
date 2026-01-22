"""项目管理路由"""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, Depends, Request

from docuflow.api.schemas.project import ProjectResponse, ProjectStatusResponse

router = APIRouter()

# 允许的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".md", ".txt"}


def get_project_service(request: Request):
    """获取项目服务"""
    return request.app.state.project_service


@router.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: Request,
    files: List[UploadFile] = File(..., description="上传的文档文件"),
    name: Optional[str] = Form(None, description="项目名称（可选，默认使用第一个文件名）"),
    description: Optional[str] = Form(None, description="项目描述"),
):
    """创建项目并上传文件

    只有 files 是必填项，其他字段可选：
    - name: 项目名称，不填则使用第一个上传文件的文件名（不含扩展名）
    - 模型使用全局配置（环境变量 DOCUFLOW_MODEL_NAME）
    """
    project_service = get_project_service(request)

    # 验证文件类型
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {ext}。支持的类型: {', '.join(ALLOWED_EXTENSIONS)}",
            )

    # 如果没有提供项目名称，使用第一个文件名
    project_name = name
    if not project_name and files:
        first_file = files[0].filename
        project_name = Path(first_file).stem  # 去掉扩展名

    # 创建项目
    project = await project_service.create_project(
        name=project_name or "未命名项目",
        description=description,
        files=files,
    )

    return project


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(request: Request):
    """获取项目列表"""
    project_service = get_project_service(request)
    return await project_service.list_projects()


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, request: Request):
    """获取项目详情"""
    project_service = get_project_service(request)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, request: Request):
    """删除项目"""
    project_service = get_project_service(request)
    success = await project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"message": "项目已删除", "project_id": project_id}


@router.get("/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str, request: Request):
    """获取项目工作流状态"""
    project_service = get_project_service(request)

    # 先检查项目是否存在
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    status = await project_service.get_project_status(project_id)
    if not status:
        raise HTTPException(status_code=404, detail="项目尚未初始化，请先启动 init 任务")

    return status
