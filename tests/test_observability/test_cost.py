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

"""Tests for the cost calculator module."""

from __future__ import annotations

from fireflyframework_genai.observability.cost import (
    CostCalculator,
    GenAIPricesCostCalculator,
    StaticPriceCostCalculator,
    get_cost_calculator,
)


class TestStaticPriceCostCalculator:
    def test_known_model_returns_nonzero(self):
        calc = StaticPriceCostCalculator()
        cost = calc.estimate("openai:gpt-4o", input_tokens=1000, output_tokens=500)
        assert cost > 0

    def test_unknown_model_returns_zero(self):
        calc = StaticPriceCostCalculator()
        cost = calc.estimate("unknown:mystery-model", input_tokens=1000, output_tokens=500)
        assert cost == 0.0

    def test_prefix_match(self):
        calc = StaticPriceCostCalculator()
        # "openai:gpt-4o-2024-08-06" should match "openai:gpt-4o"
        cost = calc.estimate("openai:gpt-4o-2024-08-06", input_tokens=1000, output_tokens=500)
        assert cost > 0

    def test_custom_prices(self):
        custom = {"custom:model-v1": (1.0, 2.0)}
        calc = StaticPriceCostCalculator(prices=custom)
        cost = calc.estimate("custom:model-v1", input_tokens=1_000_000, output_tokens=1_000_000)
        assert cost == 3.0  # 1M * 1.0/1M + 1M * 2.0/1M

    def test_zero_tokens_returns_zero(self):
        calc = StaticPriceCostCalculator()
        cost = calc.estimate("openai:gpt-4o", input_tokens=0, output_tokens=0)
        assert cost == 0.0

    def test_calculation_accuracy(self):
        calc = StaticPriceCostCalculator(prices={"test:model": (10.0, 20.0)})
        # 100 input tokens at $10/M = $0.001; 200 output at $20/M = $0.004
        cost = calc.estimate("test:model", input_tokens=100, output_tokens=200)
        assert abs(cost - 0.005) < 1e-9

    def test_satisfies_protocol(self):
        calc = StaticPriceCostCalculator()
        assert isinstance(calc, CostCalculator)


class TestGenAIPricesCostCalculator:
    def test_not_installed_returns_zero(self):
        calc = GenAIPricesCostCalculator()
        # genai-prices is likely not installed in test env
        cost = calc.estimate("openai:gpt-4o", input_tokens=1000, output_tokens=500)
        assert cost == 0.0

    def test_satisfies_protocol(self):
        calc = GenAIPricesCostCalculator()
        assert isinstance(calc, CostCalculator)


class TestGetCostCalculator:
    def test_static_preference(self):
        calc = get_cost_calculator("static")
        assert isinstance(calc, StaticPriceCostCalculator)

    def test_auto_returns_calculator(self):
        calc = get_cost_calculator("auto")
        assert isinstance(calc, CostCalculator)

    def test_default_auto(self):
        calc = get_cost_calculator()
        assert isinstance(calc, CostCalculator)
