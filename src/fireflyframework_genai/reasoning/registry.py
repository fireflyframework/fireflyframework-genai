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

"""Global reasoning pattern registry."""

from __future__ import annotations

import logging
import threading
from typing import Any

from fireflyframework_genai.exceptions import ReasoningPatternNotFoundError

logger = logging.getLogger(__name__)


class ReasoningPatternRegistry:
    """Central registry for reasoning pattern instances or classes."""

    def __init__(self) -> None:
        self._patterns: dict[str, Any] = {}
        self._lock = threading.Lock()

    def register(self, name: str, pattern: Any) -> None:
        """Register *pattern* under *name*."""
        with self._lock:
            self._patterns[name] = pattern
        logger.debug("Registered reasoning pattern '%s'", name)

    def get(self, name: str) -> Any:
        """Return the pattern registered under *name*.

        Raises:
            ReasoningPatternNotFoundError: If *name* is not registered.
        """
        with self._lock:
            try:
                return self._patterns[name]
            except KeyError:
                raise ReasoningPatternNotFoundError(f"No reasoning pattern registered with name '{name}'") from None

    def has(self, name: str) -> bool:
        with self._lock:
            return name in self._patterns

    def list_patterns(self) -> list[str]:
        with self._lock:
            return list(self._patterns.keys())

    def clear(self) -> None:
        with self._lock:
            self._patterns.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._patterns)


# Module-level singleton
reasoning_registry = ReasoningPatternRegistry()
