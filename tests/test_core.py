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

"""Tests for the core module: types, config, exceptions, plugin."""

from __future__ import annotations

from fireflyframework_genai.config import FireflyGenAIConfig
from fireflyframework_genai.exceptions import (
    AgentError,
    ConfigurationError,
    FireflyGenAIError,
    ToolError,
)
from fireflyframework_genai.types import JSON, AgentDepsT, Metadata


class TestTypes:
    def test_json_alias(self):
        # JSON is a type alias, verify it exists
        assert JSON is not None

    def test_metadata_alias(self):
        assert Metadata is not None

    def test_agent_deps_type_var(self):
        assert AgentDepsT is not None


class TestExceptions:
    def test_base_exception_hierarchy(self):
        err = FireflyGenAIError("test")
        assert isinstance(err, Exception)
        assert str(err) == "test"

    def test_agent_error_is_firefly_error(self):
        err = AgentError("agent failed")
        assert isinstance(err, FireflyGenAIError)

    def test_tool_error_is_firefly_error(self):
        err = ToolError("tool failed")
        assert isinstance(err, FireflyGenAIError)

    def test_configuration_error_is_firefly_error(self):
        err = ConfigurationError("bad config")
        assert isinstance(err, FireflyGenAIError)


class TestConfig:
    def test_config_creates_instance(self):
        config = FireflyGenAIConfig()
        assert config is not None

    def test_config_has_default_model(self):
        config = FireflyGenAIConfig()
        assert isinstance(config.default_model, str)
