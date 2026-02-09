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

"""Tools subpackage -- protocol, base class, registry, guards, composition, and built-ins."""

from fireflyframework_genai.tools.base import (
    BaseTool,
    GuardProtocol,
    GuardResult,
    ParameterSpec,
    ToolInfo,
    ToolProtocol,
)
from fireflyframework_genai.tools.builder import ToolBuilder
from fireflyframework_genai.tools.cached import CachedTool
from fireflyframework_genai.tools.composer import (
    ConditionalComposer,
    FallbackComposer,
    SequentialComposer,
)
from fireflyframework_genai.tools.decorators import firefly_tool, guarded, retryable
from fireflyframework_genai.tools.guards import (
    ApprovalGuard,
    CompositeGuard,
    RateLimitGuard,
    SandboxGuard,
    ValidationGuard,
)
from fireflyframework_genai.tools.registry import ToolRegistry, tool_registry
from fireflyframework_genai.tools.toolkit import ToolKit

__all__ = [
    "ApprovalGuard",
    "BaseTool",
    "CachedTool",
    "CompositeGuard",
    "ConditionalComposer",
    "FallbackComposer",
    "GuardProtocol",
    "GuardResult",
    "ParameterSpec",
    "RateLimitGuard",
    "SandboxGuard",
    "SequentialComposer",
    "ToolBuilder",
    "ToolInfo",
    "ToolKit",
    "ToolProtocol",
    "ToolRegistry",
    "ValidationGuard",
    "firefly_tool",
    "guarded",
    "retryable",
    "tool_registry",
]
