"""FastAPI 应用主入口"""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from docuflow.api.routers import projects, tasks, modules  # , websocket
from docuflow.api.services.project_service import ProjectService
from docuflow.api.services.task_service import TaskManager
from docuflow.api.services.notification_service import NotificationService
from docuflow.core.config import get_api_settings, get_settings
from docuflow.utils import setup_logging
from docuflow.utils.logging import set_request_context

# 配置日志
setup_logging(level=20)  # INFO 级别


class RequestContextMiddleware(BaseHTTPMiddleware):
    """请求上下文中间件 - 为每个 API 请求设置上下文"""
    
    async def dispatch(self, request: Request, call_next):
        # 生成请求ID，用于追踪API请求日志
        request_id = str(uuid.uuid4())[:8]
        
        # 从请求头或查询参数中尝试获取user_id (可选)
        user_id = request.headers.get('X-User-ID') or request.query_params.get('user_id')
        
        # 设置请求上下文
        set_request_context(request_id=request_id, user_id=user_id)
        
        response = await call_next(request)
        
        # 在响应头中返回request_id方便调试
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_api_settings()

    # 确保数据目录存在
    data_dir = Path(settings.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    # 初始化 LLM 并发控制信号量
    from docuflow.llm.client import reset_semaphore
    app_settings = get_settings()
    reset_semaphore(app_settings.llm_max_concurrent)

    # 初始化服务
    notification_service = NotificationService()
    project_service = ProjectService(data_dir)
    task_manager = TaskManager(
        project_service=project_service,
        notification_service=notification_service,
        max_workers=settings.max_workers,
    )

    # 挂载到 app.state
    app.state.notification_service = notification_service
    app.state.project_service = project_service
    app.state.task_manager = task_manager

    yield

    # 清理资源
    task_manager.shutdown()


app = FastAPI(
    title="DocuFlow-AI API",
    description="将需求文档转换为结构化设计文档的 AI 服务",
    version="0.1.0",
    lifespan=lifespan,
)

# 添加请求上下文中间件
app.add_middleware(RequestContextMiddleware)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(projects.router, prefix="/api/v1", tags=["项目管理"])
app.include_router(tasks.router, prefix="/api/v1", tags=["任务管理"])
app.include_router(modules.router, prefix="/api/v1", tags=["模块内容"])
# app.include_router(websocket.router, prefix="/api/v1", tags=["WebSocket"])  # 暂时不需要


@app.get("/api/v1/health", tags=["系统"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/api/v1/models", tags=["系统"])
async def list_models():
    """获取可用模型列表"""
    from docuflow.core.config import get_available_models

    return {"models": get_available_models()}


def run():
    """运行 API 服务"""
    settings = get_api_settings()
    uvicorn.run(
        "docuflow.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )

if __name__ == "__main__":
    run()
