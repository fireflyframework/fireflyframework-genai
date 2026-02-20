# Copyright 2026 Firefly Software Solutions Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""WebSocket endpoint for real-time pipeline execution in Firefly Studio.

Provides a ``/ws/execution`` WebSocket route that accepts JSON messages
and streams execution events back to the frontend.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect  # type: ignore[import-not-found]

logger = logging.getLogger(__name__)


def create_execution_router() -> APIRouter:
    """Create an :class:`APIRouter` with the execution WebSocket endpoint.

    Endpoints
    ---------
    ``WS /ws/execution``
        Accept a WebSocket connection.  On receiving a JSON message with
        ``"action": "run"``, respond with a stub error (execution is not
        fully wired yet).  Unknown actions also receive an error response.
    """
    router = APIRouter(tags=["execution"])

    @router.websocket("/ws/execution")
    async def execution_ws(websocket: WebSocket) -> None:
        await websocket.accept()
        logger.info("Execution WebSocket connected")

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Invalid JSON",
                        }
                    )
                    continue

                action = message.get("action")

                if action in ("run", "debug"):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": "Execution is not fully wired yet. PipelineEngine integration is pending.",
                        }
                    )
                    await websocket.send_json(
                        {
                            "type": "pipeline_complete",
                            "success": False,
                            "duration_ms": 0.0,
                            "pipeline_name": "unknown",
                        }
                    )
                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Unknown action: {action}",
                        }
                    )
        except WebSocketDisconnect:
            logger.info("Execution WebSocket disconnected")

    return router
