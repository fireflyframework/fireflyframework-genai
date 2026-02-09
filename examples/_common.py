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

"""Shared constants and utilities for all examples."""

from __future__ import annotations

import getpass
import os

MODEL = "openai:gpt-5.2-2025-12-11"
"""The OpenAI model used across all examples."""


def ensure_api_key() -> None:
    """Ensure that ``OPENAI_API_KEY`` is set.

    If the environment variable is not present, the user is prompted
    interactively via :func:`getpass.getpass` and the value is stored
    in the process environment so that Pydantic AI can pick it up.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        key = getpass.getpass("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = key
