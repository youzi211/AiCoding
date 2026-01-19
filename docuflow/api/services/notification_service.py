"""WebSocket 通知服务"""

import asyncio
from typing import Dict, Set

from fastapi import WebSocket


class NotificationService:
    """WebSocket 通知服务 - 管理连接和消息广播"""

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, project_id: str, websocket: WebSocket):
        """添加 WebSocket 连接"""
        await websocket.accept()
        async with self._lock:
            if project_id not in self.connections:
                self.connections[project_id] = set()
            self.connections[project_id].add(websocket)

    async def disconnect(self, project_id: str, websocket: WebSocket):
        """移除 WebSocket 连接"""
        async with self._lock:
            if project_id in self.connections:
                self.connections[project_id].discard(websocket)
                if not self.connections[project_id]:
                    del self.connections[project_id]

    async def broadcast(self, project_id: str, message: dict):
        """向项目的所有连接广播消息"""
        if project_id not in self.connections:
            return

        dead_connections: Set[WebSocket] = set()

        for websocket in self.connections.get(project_id, set()).copy():
            try:
                await websocket.send_json(message)
            except Exception:
                dead_connections.add(websocket)

        # 清理断开的连接
        for ws in dead_connections:
            await self.disconnect(project_id, ws)

    def get_connection_count(self, project_id: str) -> int:
        """获取项目的连接数"""
        return len(self.connections.get(project_id, set()))

    def has_connections(self, project_id: str) -> bool:
        """检查项目是否有活跃连接"""
        return project_id in self.connections and len(self.connections[project_id]) > 0
