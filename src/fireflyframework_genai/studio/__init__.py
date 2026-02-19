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

"""Firefly Studio -- visual agent IDE for the Firefly GenAI framework."""

from __future__ import annotations

from fireflyframework_genai.studio.config import StudioConfig

__all__ = [
    "StudioConfig",
    "launch_studio",
]


def launch_studio() -> None:
    """Launch the Firefly Studio server.

    .. note:: Not yet implemented.
    """
    raise NotImplementedError("Firefly Studio is not yet implemented")
