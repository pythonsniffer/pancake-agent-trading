from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime
from typing import Dict, Set

router = APIRouter()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "prices": set(),
            "trades": set(),
            "agents": set(),
            "portfolio": set(),
            "system": set(),
        }

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel in self.active_connections:
            self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)

    async def broadcast(self, channel: str, message: dict):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections[channel].discard(conn)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception:
            pass


manager = ConnectionManager()


@router.websocket("/prices")
async def websocket_prices(websocket: WebSocket):
    """WebSocket for real-time price updates"""
    await manager.connect(websocket, "prices")
    try:
        while True:
            # Keep connection alive and wait for messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                # Handle subscription requests
                if message.get("action") == "subscribe":
                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "subscribed",
                        "channel": "prices",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, "prices")


@router.websocket("/trades")
async def websocket_trades(websocket: WebSocket):
    """WebSocket for real-time trade updates"""
    await manager.connect(websocket, "trades")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("action") == "subscribe":
                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "subscribed",
                        "channel": "trades",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, "trades")


@router.websocket("/agents")
async def websocket_agents(websocket: WebSocket):
    """WebSocket for real-time agent updates"""
    await manager.connect(websocket, "agents")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "subscribed",
                        "channel": "agents",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                elif action == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, "agents")


@router.websocket("/portfolio")
async def websocket_portfolio(websocket: WebSocket):
    """WebSocket for real-time portfolio updates"""
    await manager.connect(websocket, "portfolio")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("action") == "subscribe":
                    await manager.send_personal_message({
                        "type": "subscription",
                        "status": "subscribed",
                        "channel": "portfolio",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, "portfolio")


@router.post("/broadcast/{channel}")
async def broadcast_message(channel: str, message: dict):
    """Broadcast a message to all connections in a channel"""
    message["timestamp"] = datetime.utcnow().isoformat()
    await manager.broadcast(channel, message)
    return {"status": "sent", "channel": channel}


# Background task to broadcast price updates
async def broadcast_price_update(pool_data: dict):
    """Broadcast price update to all connected clients"""
    await manager.broadcast("prices", {
        "type": "price_update",
        "data": pool_data
    })


# Background task to broadcast trade updates
async def broadcast_trade_update(trade_data: dict):
    """Broadcast trade update to all connected clients"""
    await manager.broadcast("trades", {
        "type": "trade_update",
        "data": trade_data
    })


# Background task to broadcast agent updates
async def broadcast_agent_update(agent_data: dict):
    """Broadcast agent update to all connected clients"""
    await manager.broadcast("agents", {
        "type": "agent_update",
        "data": agent_data
    })


# Background task to broadcast portfolio updates
async def broadcast_portfolio_update(portfolio_data: dict):
    """Broadcast portfolio update to all connected clients"""
    await manager.broadcast("portfolio", {
        "type": "portfolio_update",
        "data": portfolio_data
    })
