"""Execute planned tool calls against the registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from gateway.agents.planner import PlannedAction
from gateway.agents.tools import ToolRegistry
from gateway.clients.data_api import (
    DataServiceClient,
)


@dataclass
class ExecutionRecord:
    """Outcome of a single tool execution."""

    tool: str
    params: dict[str, Any] = field(
        default_factory=dict,
    )
    rationale: str = ""
    outcome: dict[str, Any] | None = None
    error: str | None = None


class ActionExecutor:
    """Run a list of planned tool calls."""

    def run_plan(
        self,
        plan: list[PlannedAction],
        registry: ToolRegistry,
        client: DataServiceClient | None = None,
    ) -> tuple[
        list[dict[str, Any]],
        list[ExecutionRecord],
    ]:
        """Execute each action and collect results.

        Returns a tuple of (collected_data, log).
        """
        collected: list[dict[str, Any]] = []
        log: list[ExecutionRecord] = []

        for action in plan:
            record = ExecutionRecord(
                tool=action.tool,
                params=action.params,
                rationale=action.rationale,
            )

            handler = registry.get(action.tool)
            if handler is None:
                record.error = f"Tool not found: {action.tool}"
                log.append(record)
                logger.warning(
                    "Skipped unknown tool: {}",
                    action.tool,
                )
                continue

            try:
                result = handler(**action.params)
                record.outcome = (
                    result if isinstance(result, dict) else {"data": result}
                )
                collected.append(record.outcome)
                logger.info(
                    "Executed tool: {}",
                    action.tool,
                )
            except Exception as exc:
                record.error = str(exc)
                logger.error(
                    "Tool {} failed: {}",
                    action.tool,
                    exc,
                )

            log.append(record)

        followups = self._generate_followups(
            collected,
            registry,
            client,
        )
        collected.extend(followups)

        return collected, log

    @staticmethod
    def _generate_followups(
        results: list[dict[str, Any]],
        registry: ToolRegistry,
        client: DataServiceClient | None,
    ) -> list[dict[str, Any]]:
        """Derive follow-up calls from results."""
        followup_data: list[dict[str, Any]] = []
        if client is None:
            return followup_data

        for result in results:
            names = result.get(
                "related_people",
                [],
            )
            for name in names[:2]:
                handler = registry.get(
                    "query_team",
                )
                if handler is None:
                    continue
                try:
                    data = handler(name=name)
                    followup_data.append(data)
                except Exception:
                    pass

            companies = result.get(
                "related_companies",
                [],
            )
            for company in companies[:2]:
                handler = registry.get(
                    "query_portfolio",
                )
                if handler is None:
                    continue
                try:
                    data = handler(company=company)
                    followup_data.append(data)
                except Exception:
                    pass

        return followup_data

    @staticmethod
    def format_trace(
        log: list[ExecutionRecord],
    ) -> list[dict[str, Any]]:
        """Convert execution log to serialisable."""
        entries: list[dict[str, Any]] = []
        for rec in log:
            entry: dict[str, Any] = {
                "tool": rec.tool,
                "params": rec.params,
                "rationale": rec.rationale,
            }
            if rec.error:
                entry["error"] = rec.error
            else:
                entry["status"] = "success"
            entries.append(entry)
        return entries
