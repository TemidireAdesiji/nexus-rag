"""Tool registry for agentic operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from loguru import logger

from gateway.clients.data_api import (
    DataServiceClient,
)


class ToolRegistry:
    """Maintains a catalogue of callable tools."""

    def __init__(self) -> None:
        self._tools: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        handler: Callable[..., Any],
        description: str = "",
    ) -> None:
        """Add a tool to the registry."""
        self._tools[name] = {
            "handler": handler,
            "description": description,
        }
        logger.debug(
            "Registered tool: {}",
            name,
        )

    def get(
        self,
        name: str,
    ) -> Callable[..., Any] | None:
        """Retrieve the handler for a tool."""
        entry = self._tools.get(name)
        if entry is None:
            return None
        return entry["handler"]  # type: ignore[no-any-return]

    def catalog(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def descriptions(
        self,
    ) -> list[dict[str, str]]:
        """Tool names with their descriptions."""
        return [
            {
                "name": name,
                "description": info["description"],
            }
            for name, info in self._tools.items()
        ]

    @classmethod
    def build_from_client(
        cls,
        client: DataServiceClient,
    ) -> ToolRegistry:
        """Auto-register tools from a data client."""
        registry = cls()

        tool_defs: list[tuple[str, str, str]] = [
            (
                "query_team",
                "name",
                "Look up team member details",
            ),
            (
                "query_team_analysis",
                "name",
                "Analyse team member performance",
            ),
            (
                "query_portfolio",
                "company",
                "Retrieve portfolio company data",
            ),
            (
                "query_portfolio_analysis",
                "company",
                "Analyse portfolio company",
            ),
            (
                "query_verticals",
                "sector",
                "Query industry vertical info",
            ),
            (
                "query_engagements",
                "name",
                "Fetch engagement records",
            ),
            (
                "query_web_content",
                "url",
                "Retrieve web page content",
            ),
        ]

        for tool_name, _, desc in tool_defs:
            method = getattr(
                client,
                tool_name,
                None,
            )
            if method is not None:
                registry.register(
                    tool_name,
                    method,
                    desc,
                )

        logger.info(
            "Built registry with {} tools from data client",
            len(registry._tools),
        )
        return registry
