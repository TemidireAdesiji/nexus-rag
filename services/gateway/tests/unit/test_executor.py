"""Tests for the action executor."""

from __future__ import annotations

from gateway.agents.executor import (
    ActionExecutor,
    ExecutionRecord,
)
from gateway.agents.planner import PlannedAction
from gateway.agents.tools import ToolRegistry


def _registry() -> ToolRegistry:
    """Registry with simple handlers."""
    reg = ToolRegistry()
    reg.register(
        "echo",
        lambda text="": {"echoed": text},
        "Echo tool",
    )
    reg.register(
        "failing",
        lambda: (_ for _ in ()).throw(
            RuntimeError("boom"),
        ),
        "Always fails",
    )
    return reg


def test_successful_execution() -> None:
    """Successful tool returns data."""
    executor = ActionExecutor()
    plan = [
        PlannedAction(
            tool="echo",
            params={"text": "hello"},
            rationale="test",
        ),
    ]
    data, log = executor.run_plan(
        plan,
        _registry(),
    )
    assert len(data) >= 1
    assert data[0]["echoed"] == "hello"


def test_missing_tool_logged() -> None:
    """Unknown tool is recorded as an error."""
    executor = ActionExecutor()
    plan = [
        PlannedAction(
            tool="nonexistent",
            params={},
            rationale="test",
        ),
    ]
    data, log = executor.run_plan(
        plan,
        _registry(),
    )
    assert log[0].error is not None
    assert "not found" in log[0].error


def test_failing_tool_is_handled() -> None:
    """Exception in tool is captured."""
    reg = ToolRegistry()
    reg.register(
        "bad",
        lambda: 1 / 0,
        "Division error",
    )
    executor = ActionExecutor()
    plan = [
        PlannedAction(
            tool="bad",
            params={},
            rationale="t",
        ),
    ]
    data, log = executor.run_plan(plan, reg)
    assert log[0].error is not None


def test_multiple_actions_executed() -> None:
    """Multiple actions all run."""
    executor = ActionExecutor()
    plan = [
        PlannedAction(
            tool="echo",
            params={"text": "a"},
            rationale="first",
        ),
        PlannedAction(
            tool="echo",
            params={"text": "b"},
            rationale="second",
        ),
    ]
    data, log = executor.run_plan(
        plan,
        _registry(),
    )
    assert len(log) == 2


def test_format_trace_success() -> None:
    """Trace formatting works for success."""
    records = [
        ExecutionRecord(
            tool="echo",
            params={"text": "x"},
            rationale="test",
            outcome={"echoed": "x"},
        ),
    ]
    trace = ActionExecutor.format_trace(records)
    assert trace[0]["status"] == "success"


def test_format_trace_error() -> None:
    """Trace formatting includes error."""
    records = [
        ExecutionRecord(
            tool="bad",
            params={},
            rationale="test",
            error="Something broke",
        ),
    ]
    trace = ActionExecutor.format_trace(records)
    assert "error" in trace[0]


def test_empty_plan_returns_empty() -> None:
    """Empty plan produces empty results."""
    executor = ActionExecutor()
    data, log = executor.run_plan(
        [],
        _registry(),
    )
    assert data == []
    assert log == []


def test_execution_record_defaults() -> None:
    """ExecutionRecord has correct defaults."""
    rec = ExecutionRecord(tool="t")
    assert rec.params == {}
    assert rec.outcome is None
    assert rec.error is None
