"""依赖注入"""

from fastapi import Request

from docuflow.api.services.project_service import ProjectService
from docuflow.api.services.task_service import TaskManager
from docuflow.api.services.notification_service import NotificationService


def get_project_service(request: Request) -> ProjectService:
    """获取项目服务"""
    return request.app.state.project_service


def get_task_manager(request: Request) -> TaskManager:
    """获取任务管理器"""
    return request.app.state.task_manager


def get_notification_service(request: Request) -> NotificationService:
    """获取通知服务"""
    return request.app.state.notification_service
