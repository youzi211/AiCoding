"""任务管理路由"""

from typing import List

from fastapi import APIRouter, HTTPException, Request

from docuflow.api.schemas.task import TaskCreateRequest, TaskResponse, TaskStatus
from docuflow.core.config import get_settings, get_available_models
from docuflow.utils import validate_user_id

router = APIRouter()


def get_task_manager(request: Request):
    """获取任务管理器"""
    return request.app.state.task_manager


def get_project_service(request: Request):
    """获取项目服务"""
    return request.app.state.project_service


@router.post("/users/{user_id}/projects/{project_id}/tasks", response_model=TaskResponse)
async def create_task(
    user_id: str,
    project_id: str,
    task_request: TaskCreateRequest,
    request: Request,
):
    """启动工作流任务"""
    user_id = validate_user_id(user_id)
    task_manager = get_task_manager(request)
    project_service = get_project_service(request)

    # 检查项目是否存在
    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查是否有正在运行的任务（只检查当前用户的）
    running_tasks = [
        t
        for t in task_manager.get_project_tasks(project_id, user_id=user_id)
        if t.status in [TaskStatus.PENDING, TaskStatus.RUNNING]
    ]
    if running_tasks:
        raise HTTPException(
            status_code=400,
            detail=f"项目已有正在运行的任务: {running_tasks[0].id}",
        )

    # 提交任务
    settings = get_settings()

    # 确定使用的模型
    model_name = task_request.model_name or settings.model_name
    available_models = get_available_models()
    if model_name not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型: {model_name}。可用模型: {', '.join(available_models)}",
        )

    task = await task_manager.submit_task(
        user_id=user_id,
        project_id=project_id,
        task_type=task_request.task_type,
        model_name=model_name,
        step_by_step=task_request.step_by_step,
    )

    return task.to_response()


@router.get("/users/{user_id}/projects/{project_id}/tasks", response_model=List[TaskResponse])
async def list_tasks(user_id: str, project_id: str, request: Request):
    """获取项目的任务列表（只返回当前用户的任务）"""
    user_id = validate_user_id(user_id)
    task_manager = get_task_manager(request)
    project_service = get_project_service(request)

    # 检查项目是否存在且属于当前用户
    project = await project_service.get_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 只获取当前用户的任务
    tasks = task_manager.get_project_tasks(project_id, user_id=user_id)
    return [t.to_response() for t in tasks]


@router.get("/users/{user_id}/projects/{project_id}/tasks/{task_id}", response_model=TaskResponse)
async def get_task(user_id: str, project_id: str, task_id: str, request: Request):
    """获取任务状态（验证所有权）"""
    user_id = validate_user_id(user_id)
    task_manager = get_task_manager(request)

    task = task_manager.get_task(task_id)

    # 验证三个条件：1. 任务存在  2. project_id 匹配  3. user_id 匹配
    if not task or task.project_id != project_id or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="任务不存在")

    return task.to_response()


@router.delete("/users/{user_id}/projects/{project_id}/tasks/{task_id}")
async def cancel_task(user_id: str, project_id: str, task_id: str, request: Request):
    """取消任务（验证所有权）"""
    user_id = validate_user_id(user_id)
    task_manager = get_task_manager(request)

    task = task_manager.get_task(task_id)

    # 验证所有权
    if not task or task.project_id != project_id or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"任务状态为 {task.status.value}，无法取消",
        )

    success = task_manager.cancel_task(task_id)
    if success:
        return {"message": "任务取消请求已发送", "task_id": task_id}
    else:
        raise HTTPException(status_code=500, detail="取消任务失败")
