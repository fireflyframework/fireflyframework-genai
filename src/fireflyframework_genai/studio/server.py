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

"""FastAPI application factory for Firefly Studio.

Call :func:`create_studio_app` to get a fully-configured FastAPI instance
with health, registry, project, and execution endpoints.
"""

from __future__ import annotations

import importlib.metadata
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)

_ALLOWED_ORIGINS: list[str] = [
    "http://localhost:5173",
    "http://localhost:4173",
    "tauri://localhost",
]


@asynccontextmanager
async def _lifespan(app: Any) -> AsyncIterator[None]:
    """FastAPI lifespan: startup and shutdown hooks for Studio."""
    # -- Startup -----------------------------------------------------------
    logger.info("Firefly Studio starting up")
    yield
    # -- Shutdown ----------------------------------------------------------
    logger.info("Firefly Studio shutting down")


def create_studio_app(
    config: Any | None = None,
) -> Any:
    """Create a FastAPI application for Firefly Studio.

    Parameters:
        config: Optional :class:`~fireflyframework_genai.studio.config.StudioConfig`.
            When *None*, a default ``StudioConfig()`` is created.

    Returns:
        A configured :class:`fastapi.FastAPI` instance.
    """
    # Lazy imports -- FastAPI and its dependencies are optional extras.
    from fastapi import FastAPI  # type: ignore[import-not-found]
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-not-found]

    from fireflyframework_genai.studio.config import StudioConfig

    if config is None:
        config = StudioConfig()

    pkg_version = importlib.metadata.version("fireflyframework-genai")

    app = FastAPI(
        title="Firefly Studio",
        version=pkg_version,
        lifespan=_lifespan,
    )

    # -- CORS middleware ---------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Health endpoint ---------------------------------------------------
    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": pkg_version}

    # -- Registry endpoints ------------------------------------------------
    from fireflyframework_genai.studio.api.registry import create_registry_router

    app.include_router(create_registry_router())

    # -- Project endpoints -------------------------------------------------
    from fireflyframework_genai.studio.api.projects import create_projects_router
    from fireflyframework_genai.studio.projects import ProjectManager

    project_manager = ProjectManager(config.projects_dir)
    app.include_router(create_projects_router(project_manager))

    # -- Code generation endpoints -----------------------------------------
    from fireflyframework_genai.studio.api.codegen import create_codegen_router

    app.include_router(create_codegen_router())

    # -- Monitoring endpoints ----------------------------------------------
    from fireflyframework_genai.studio.api.monitoring import create_monitoring_router

    app.include_router(create_monitoring_router())

    # -- Checkpoint endpoints ----------------------------------------------
    from fireflyframework_genai.studio.api.checkpoints import create_checkpoints_router
    from fireflyframework_genai.studio.execution.checkpoint import CheckpointManager

    checkpoint_manager = CheckpointManager()
    app.include_router(create_checkpoints_router(checkpoint_manager))
    app.state.checkpoint_manager = checkpoint_manager

    # -- Execution WebSocket -----------------------------------------------
    from fireflyframework_genai.studio.api.execution import create_execution_router

    app.include_router(create_execution_router())

    # -- Assistant WebSocket -----------------------------------------------
    from fireflyframework_genai.studio.api.assistant import create_assistant_router

    app.include_router(create_assistant_router())

    # Store config on app state for downstream routers
    app.state.studio_config = config

    return app
