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

"""Tests for the Studio assistant WebSocket API."""

from __future__ import annotations

import os

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed")
pytest.importorskip("httpx", reason="httpx not installed")

from starlette.testclient import TestClient

from fireflyframework_genai.studio.server import create_studio_app


@pytest.fixture()
def app(monkeypatch):
    # The studio assistant agent requires an LLM API key at construction
    # time.  Provide a dummy key so that agent creation succeeds in tests.
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return create_studio_app()


class TestAssistantWebSocket:
    def test_assistant_ws_accepts_connection(self, app):
        client = TestClient(app)
        with client.websocket_connect("/ws/assistant") as ws:
            # Connection accepted -- just close cleanly
            pass

    def test_assistant_ws_invalid_json(self, app):
        client = TestClient(app)
        with client.websocket_connect("/ws/assistant") as ws:
            ws.send_text("not json")
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Invalid JSON" in response["message"]

    def test_assistant_ws_unknown_action(self, app):
        client = TestClient(app)
        with client.websocket_connect("/ws/assistant") as ws:
            ws.send_json({"action": "unknown"})
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Unknown action" in response["message"]

    def test_assistant_ws_empty_chat_message(self, app):
        client = TestClient(app)
        with client.websocket_connect("/ws/assistant") as ws:
            ws.send_json({"action": "chat", "message": ""})
            response = ws.receive_json()
            assert response["type"] == "error"
            assert "Empty message" in response["message"]

    def test_assistant_ws_clear_history(self, app):
        client = TestClient(app)
        with client.websocket_connect("/ws/assistant") as ws:
            ws.send_json({"action": "clear_history"})
            response = ws.receive_json()
            assert response["type"] == "history_cleared"
