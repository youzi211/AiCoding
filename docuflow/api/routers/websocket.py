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
    - module_complete: 模块处理完成（包含批判信息）
    - module_error: 模块处理失败
    - critique_result: 批判评估结果
    - regenerate_start: 基于批判重新生成开始
    - error: 错误通知
    - task_complete: 任务完成

    消息格式:
    {
        "type": "event_type",
        "timestamp": "2024-01-19T12:00:00Z",
        "task_id": "uuid",
        "data": {...}
    }

    事件 data 示例:
    - module_start: {"module": "模块名"}
    - module_complete: {"module": "模块名", "critique_iterations": 2, "critique_score": 0.85, "critique_passed": true}
    - module_error: {"module": "模块名", "error": "错误信息"}
    - critique_result: {"module": "模块名", "iteration": 1, "score": 0.6, "passed": false}
    - regenerate_start: {"module": "模块名", "iteration": 1}
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