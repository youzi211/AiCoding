"""WebSocket 路由"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    project_id: str,
):
    """WebSocket 实时状态推送

    连接后，客户端将自动接收该项目的所有状态更新事件。

    事件类型:
    - phase_change: 阶段变更
    - module_start: 模块开始处理
    - module_complete: 模块处理完成
    - error: 错误通知
    - task_complete: 任务完成

    消息格式:
    {
        "type": "event_type",
        "timestamp": "2024-01-19T12:00:00Z",
        "task_id": "uuid",
        "data": {...}
    }
    """
    # 通过 websocket.app 访问 app.state
    notification_service = websocket.app.state.notification_service

    await notification_service.connect(project_id, websocket)

    try:
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await notification_service.disconnect(project_id, websocket)
    except Exception:
        await notification_service.disconnect(project_id, websocket)