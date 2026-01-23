"""日志配置"""
import logging
import sys
import uuid
from contextvars import ContextVar
from pathlib import Path
from typing import Optional, Dict, Any

# 任务上下文变量，线程安全
task_context: ContextVar[Dict[str, Any]] = ContextVar('task_context', default={})


class TaskContextFilter(logging.Filter):
    """任务上下文过滤器 - 将上下文信息注入日志记录"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """注入任务上下文到日志记录"""
        ctx = task_context.get()
        record.task_id = ctx.get('task_id', '-')
        record.user_id = ctx.get('user_id', '-')
        record.project_id = ctx.get('project_id', '-')
        record.request_id = ctx.get('request_id', '-')
        return True


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """配置并返回应用日志器"""
    logger = logging.getLogger("docuflow")
    logger.setLevel(level)
    logger.handlers.clear()

    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | [%(user_id)s/%(project_id)s/%(task_id)s] %(message)s"

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    task_filter = TaskContextFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(task_filter)
    logger.addHandler(console_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.addFilter(task_filter)
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """获取应用日志器"""
    return logging.getLogger("docuflow")


def set_task_context(task_id: str, user_id: str, project_id: str, request_id: str = None) -> None:
    """设置任务上下文"""
    task_context.set({
        'task_id': task_id,
        'user_id': user_id,
        'project_id': project_id,
        'request_id': request_id or str(uuid.uuid4())[:8]
    })


def set_request_context(request_id: str = None, user_id: str = None) -> None:
    """设置请求上下文（用于 API 请求）"""
    ctx = task_context.get().copy() if task_context.get() else {}
    ctx.update({
        'request_id': request_id or str(uuid.uuid4())[:8],
        'user_id': user_id or ctx.get('user_id', '-'),
        'task_id': ctx.get('task_id', 'api'),
        'project_id': ctx.get('project_id', '-')
    })
    task_context.set(ctx)


def get_context() -> Dict[str, Any]:
    """获取当前任务上下文"""
    return task_context.get()
