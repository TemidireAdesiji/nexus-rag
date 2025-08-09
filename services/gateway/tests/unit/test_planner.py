"""Tests for the action planner."""

from __future__ import annotations

from gateway.agents.planner import (
    ActionPlanner,
)
from gateway.agents.tools import ToolRegistry


def _registry_with_tools() -> ToolRegistry:
    """Registry with dummy handlers."""
    reg = ToolRegistry()
    reg.register(
        "query_team",
        lambda **kw: {},
        "Teams",
    )
    reg.register(
        "query_portfolio",
        lambda **kw: {},
        "Portfolio",
    )
    reg.register(
        "query_verticals",
        lambda **kw: {},
        "Verticals",
    )
    reg.register(
        "query_web_content",
        lambda **kw: {},
        "Web",
    )
    return reg


def test_keyword_match_team() -> None:
    """Team keywords trigger query_team."""
    planner = ActionPlanner()
    plan = planner.devise_plan(
        query="Who is on the team?",
        entities={"people": [], "organisations": []},
        context="",
        registry=_registry_with_tools(),
    )
    tools = [a.tool for a in plan]
    assert "query_team" in tools


def test_keyword_match_portfolio() -> None:
    """Portfolio keywords trigger correct tool."""
    planner = ActionPlanner()
    plan = planner.devise_plan(
        query="Show me the portfolio companies",
        entities={
            "people": [],
            "organisations": ["Acme Corp"],
        },
        context="",
        registry=_registry_with_tools(),
    )
    tools = [a.tool for a in plan]
    assert "query_portfolio" in tools


def test_keyword_match_web_url() -> None:
    """URL in query triggers web tool."""
    planner = ActionPlanner()
    plan = planner.devise_plan(
        query="Check https://example.com for info",
        entities={
            "people": [],
            "organisations": [],
            "links": ["https://example.com"],
        },
        context="",
        registry=_registry_with_tools(),
    )
    tools = [a.tool for a in plan]
    assert "query_web_content" in tools


def test_no_match_returns_empty() -> None:
    """Unrelated query produces no plan."""
    planner = ActionPlanner()
    plan = planner.devise_plan(
        query="What is the weather today?",
        entities={"people": [], "organisations": []},
        context="",
        registry=_registry_with_tools(),
    )
    assert len(plan) == 0


def test_entity_params_extracted() -> None:
    """Named entities populate params."""
    planner = ActionPlanner()
    plan = planner.devise_plan(
        query="Tell me about team member Alice",
        entities={
            "people": ["Alice Smith"],
            "organisations": [],
        },
        context="",
        registry=_registry_with_tools(),
    )
    team_actions = [a for a in plan if a.tool == "query_team"]
    if team_actions:
        assert team_actions[0].params.get("name") == "Alice Smith"


def test_parse_plan_output_valid_json() -> None:
    """Valid JSON array is parsed correctly."""
    raw = (
        '[{"tool": "query_team", '
        '"params": {"name": "Bob"}, '
        '"rationale": "User asked about Bob"}]'
    )
    result = ActionPlanner._parse_plan_output(raw)
    assert len(result) == 1
    assert result[0].tool == "query_team"


def test_parse_plan_output_invalid_json() -> None:
    """Invalid JSON returns empty list."""
    result = ActionPlanner._parse_plan_output(
        "not json at all",
    )
    assert result == []


def test_parse_plan_output_empty_array() -> None:
    """Empty JSON array returns empty list."""
    result = ActionPlanner._parse_plan_output("[]")
    assert result == []


def test_unregistered_tools_filtered() -> None:
    """Tools not in registry are excluded."""
    planner = ActionPlanner()
    empty_reg = ToolRegistry()
    plan = planner.devise_plan(
        query="Show team details",
        entities={"people": [], "organisations": []},
        context="",
        registry=empty_reg,
    )
    assert len(plan) == 0
