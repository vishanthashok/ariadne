"""WebSocket connection manager for simulation streaming."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import WebSocket

from api.schemas import SimulationConfig
from api.simulation import SimulationEngine


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def send_json(self, websocket: WebSocket, data: Any) -> None:
        await websocket.send_json(data)


manager = ConnectionManager()


async def simulation_loop(websocket: WebSocket, engine: SimulationEngine) -> None:
    engine.start()
    base_interval = 0.5  # 2 Hz visual frames
    try:
        while True:
            # Non-blocking control messages
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                data = json.loads(msg)
                action = data.get("action")
                value = data.get("value")
                if action == "set_speed":
                    engine.apply_control("set_speed", value)
                elif action == "toggle_jamming":
                    engine.apply_control("toggle_jamming", value)
                elif action == "set_noise":
                    engine.apply_control("set_noise", value)
                elif action == "set_altitude":
                    engine.apply_control("set_altitude", value)
                elif action == "pause":
                    engine.apply_control("pause")
                elif action == "play":
                    engine.apply_control("play")
                elif action == "restart":
                    engine.apply_control("restart")
            except asyncio.TimeoutError:
                pass
            except Exception:
                break

            if engine.paused:
                await asyncio.sleep(0.1)
                continue

            frame = engine.step()
            if frame is None:
                if not engine.running:
                    await websocket.send_json({"type": "ended"})
                    # auto-restart for continuous demo
                    engine.restart()
                    continue
                await asyncio.sleep(0.05)
                continue

            await websocket.send_json({"type": "frame", "data": frame.model_dump()})
            interval = base_interval / max(0.1, engine.config.speed)
            await asyncio.sleep(interval)
    except Exception:
        pass
    finally:
        engine.stop()
        manager.disconnect(websocket)
