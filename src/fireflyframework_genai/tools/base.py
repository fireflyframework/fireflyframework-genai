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

"""Tool abstraction layer: protocol, base class, and data models.

The tools system uses a three-layer extensibility model:

1. :class:`ToolProtocol` -- a ``typing.Protocol`` that any object can satisfy
   via duck typing.
2. :class:`BaseTool` -- an abstract base class that provides guard execution,
   validation, error handling, and logging out of the box.
3. Concrete implementations (built-in tools, user-defined subclasses).

Users who prefer composition can implement :class:`ToolProtocol` directly.
Users who prefer inheritance can subclass :class:`BaseTool` and override
:meth:`~BaseTool._execute`.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from fireflyframework_genai.exceptions import ToolError, ToolTimeoutError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


class ParameterSpec(BaseModel):
    """Describes a single parameter accepted by a tool."""

    name: str
    type_annotation: str
    description: str = ""
    required: bool = True
    default: Any = None


class ToolInfo(BaseModel):
    """Lightweight, serialisable summary of a registered tool."""

    name: str
    description: str
    tags: list[str] = []
    parameter_count: int = 0


class GuardResult(BaseModel):
    """Outcome of a :class:`GuardProtocol` check.

    When *passed* is ``False``, *reason* explains why the guard rejected
    the execution.
    """

    passed: bool
    reason: str | None = None


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------


@runtime_checkable
class ToolProtocol(Protocol):
    """Minimal contract that any tool must satisfy.

    Implement this protocol to create tools that integrate with the
    Firefly tool registry and composition system without inheriting from
    any framework class.
    """

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    async def execute(self, **kwargs: Any) -> Any:
        """Run the tool with the given keyword arguments."""
        ...


@runtime_checkable
class GuardProtocol(Protocol):
    """Pre-execution guard that can accept or reject a tool invocation."""

    async def check(self, tool_name: str, kwargs: dict[str, Any]) -> GuardResult:
        """Evaluate whether execution should proceed."""
        ...


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class BaseTool(ABC):
    """Abstract base class for Firefly tools.

    Subclasses must implement :meth:`_execute`.  The public :meth:`execute`
    method wraps it with guard evaluation, logging, and error handling.

    Parameters:
        name: Unique tool name.
        description: Human-readable explanation of what the tool does.
        tags: Tags for capability-based discovery in the registry.
        guards: Ordered sequence of guards evaluated before execution.
        parameters: Declared parameter specifications (used by builder /
            schema generation).
    """

    def __init__(
        self,
        name: str,
        *,
        description: str = "",
        tags: Sequence[str] = (),
        guards: Sequence[GuardProtocol] = (),
        parameters: Sequence[ParameterSpec] = (),
        timeout: float | None = None,
    ) -> None:
        self._name = name
        self._description = description
        self._tags = list(tags)
        self._guards = list(guards)
        self._parameters = list(parameters)
        self._timeout = timeout

    # -- Properties ----------------------------------------------------------

    @property
    def name(self) -> str:
        """Unique tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Human-readable description."""
        return self._description

    @property
    def tags(self) -> list[str]:
        """Tags for capability-based discovery."""
        return self._tags

    @property
    def guards(self) -> list[GuardProtocol]:
        """Ordered guard chain evaluated before execution."""
        return self._guards

    @property
    def parameters(self) -> list[ParameterSpec]:
        """Declared parameter specifications."""
        return self._parameters

    # -- Execution -----------------------------------------------------------

    async def execute(self, **kwargs: Any) -> Any:
        """Run the tool after evaluating all guards.

        If any guard rejects, a :class:`ToolError` is raised immediately.
        When a *timeout* is configured, wraps the execution in
        :func:`asyncio.wait_for` and raises :class:`ToolTimeoutError`
        on expiry.
        """
        for guard in self._guards:
            result = await guard.check(self._name, kwargs)
            if not result.passed:
                raise ToolError(f"Guard rejected execution of tool '{self._name}': {result.reason}")

        logger.debug("Executing tool '%s' with kwargs=%s", self._name, list(kwargs.keys()))
        try:
            if self._timeout is not None:
                return await asyncio.wait_for(
                    self._execute(**kwargs),
                    timeout=self._timeout,
                )
            return await self._execute(**kwargs)
        except TimeoutError:
            raise ToolTimeoutError(f"Tool '{self._name}' timed out after {self._timeout}s") from None
        except ToolError:
            raise
        except Exception as exc:
            raise ToolError(f"Tool '{self._name}' failed: {exc}") from exc

    def pydantic_handler(self) -> Any:
        """Return a callable suitable for :class:`pydantic_ai.Tool`.

        By default this returns :meth:`execute`.  Subclasses that wrap a
        typed handler (e.g. decorated tools) should override this to
        return a wrapper preserving the original function's signature so
        that Pydantic AI can generate correct JSON schemas for the LLM.
        """
        return self.execute

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> Any:
        """Subclass hook -- implement the actual tool logic here."""
        ...

    # -- Info ----------------------------------------------------------------

    def info(self) -> ToolInfo:
        """Return a serialisable summary of this tool."""
        return ToolInfo(
            name=self._name,
            description=self._description,
            tags=self._tags,
            parameter_count=len(self._parameters),
        )

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self._name!r})"
