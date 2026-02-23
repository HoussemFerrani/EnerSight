"""
WebSocket endpoint for real-time energy data streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import json
import asyncio
from backend.services.data_simulator import get_simulator

router = APIRouter()

# Store active connections
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.simulator = get_simulator()
        self.broadcast_task = None
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Start broadcasting if this is the first connection
        if len(self.active_connections) == 1 and not self.broadcast_task:
            self.broadcast_task = asyncio.create_task(self.start_broadcasting())
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        
        # Stop broadcasting if no connections remain
        if len(self.active_connections) == 0:
            self.simulator.stop()
            if self.broadcast_task:
                self.broadcast_task.cancel()
                self.broadcast_task = None
    
    async def send_to_connection(self, websocket: WebSocket, data: dict):
        """Send data to a specific connection."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"Error sending to connection: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, data: dict):
        """Broadcast data to all active connections."""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def start_broadcasting(self):
        """Start streaming simulated data to all connections."""
        async def broadcast_callback(reading: dict):
            """Callback for simulator to broadcast readings."""
            await self.broadcast({
                "type": "energy_reading",
                "data": reading
            })
        
        # Stream data every 5 seconds
        await self.simulator.stream_data(broadcast_callback, interval=5.0)


# Singleton connection manager
manager = ConnectionManager()


@router.websocket("/ws/energy/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time energy data.
    
    Clients connect to this endpoint to receive live energy readings
    every 5 seconds.
    
    Example client usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/energy/live');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('New reading:', data);
    };
    ```
    """
    await manager.connect(websocket)
    
    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for any client messages (ping/pong, etc.)
            data = await websocket.receive_text()
            
            # Echo back acknowledgment
            await websocket.send_json({
                "type": "ack",
                "message": "Message received"
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/energy/live/status")
async def get_live_status():
    """Get status of live data streaming."""
    return {
        "active_connections": len(manager.active_connections),
        "streaming": manager.simulator.is_running,
        "update_interval": "5 seconds"
    }
