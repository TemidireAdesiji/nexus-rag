"""Tool-call planning via keywords and LLM."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_core.output_parsers import (
    StrOutputParser,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
)
from loguru import logger

from gateway.agents.tools import ToolRegistry
from gateway.generation.prompts import (
    TOOL_PLANNING_TEMPLATE,
)


@dataclass
class PlannedAction:
    """A single planned tool invocation."""

    tool: str
    params: dict[str, Any] = field(
        default_factory=dict,
    )
    rationale: str = ""


class ActionPlanner:
    """Decide which tools to invoke for a query."""

    _KEYWORD_MAP: dict[str, list[str]] = {
        "query_team": [
            "team",
            "member",
            "employee",
            "staff",
            "personnel",
            "who is",
        ],
        "query_team_analysis": [
            "team analysis",
            "performance review",
            "team performance",
        ],
        "query_portfolio": [
            "portfolio",
            "company",
            "investment",
            "holding",
        ],
        "query_portfolio_analysis": [
            "portfolio analysis",
            "company analysis",
            "investment analysis",
        ],
        "query_verticals": [
            "vertical",
            "sector",
            "industry",
            "market segment",
        ],
        "query_engagements": [
            "engagement",
            "project",
            "assignment",
            "deal",
        ],
        "query_web_content": [
            "http://",
            "https://",
            "website",
            "web page",
            "url",
        ],
    }

    def __init__(
        self,
        llm: object | None = None,
    ) -> None:
        self._llm = llm

    def devise_plan(
        self,
        query: str,
        entities: dict[str, list[str]],
        context: str,
        registry: ToolRegistry,
    ) -> list[PlannedAction]:
        """Create a tool execution plan."""
        keyword_actions = self._keyword_plan(
            query,
            entities,
            context,
        )

        if keyword_actions:
            available = set(registry.catalog())
            return [a for a in keyword_actions if a.tool in available]

        if self._llm is not None:
            llm_actions = self._llm_plan(
                query,
                entities,
                context,
                registry.catalog(),
            )
            if llm_actions:
                return llm_actions

        return []

    def _keyword_plan(
        self,
        query: str,
        entities: dict[str, list[str]],
        context: str,
    ) -> list[PlannedAction]:
        """Match tools using keyword heuristics."""
        lower_q = query.lower()
        actions: list[PlannedAction] = []

        for tool, keywords in self._KEYWORD_MAP.items():
            if not any(kw in lower_q for kw in keywords):
                continue

            params = self._infer_params(
                tool,
                query,
                entities,
            )
            actions.append(
                PlannedAction(
                    tool=tool,
                    params=params,
                    rationale=("Keyword match in query"),
                ),
            )

        return actions

    @staticmethod
    def _infer_params(
        tool: str,
        query: str,
        entities: dict[str, list[str]],
    ) -> dict[str, Any]:
        """Extract parameters from entities."""
        people = entities.get("people", [])
        orgs = entities.get("organisations", [])
        industries = entities.get(
            "industries",
            [],
        )
        links = entities.get("links", [])

        if (
            tool
            in (
                "query_team",
                "query_team_analysis",
                "query_engagements",
            )
            and people
        ):
            return {"name": people[0]}

        if (
            tool
            in (
                "query_portfolio",
                "query_portfolio_analysis",
            )
            and orgs
        ):
            return {"company": orgs[0]}

        if tool == "query_verticals" and industries:
            return {"sector": industries[0]}

        if tool == "query_web_content" and links:
            return {"url": links[0]}

        return {}

    def _llm_plan(
        self,
        query: str,
        entities: dict[str, list[str]],
        context: str,
        tool_names: list[str],
    ) -> list[PlannedAction]:
        """Use LLM to decide which tools to call."""
        try:
            prompt = ChatPromptTemplate.from_template(
                TOOL_PLANNING_TEMPLATE,
            )
            chain = (
                prompt
                | self._llm  # type: ignore[arg-type]
                | StrOutputParser()
            )
            raw = chain.invoke(
                {
                    "tool_names": ", ".join(
                        tool_names,
                    ),
                    "people": ", ".join(
                        entities.get("people", []),
                    ),
                    "organisations": ", ".join(
                        entities.get(
                            "organisations",
                            [],
                        ),
                    ),
                    "industries": ", ".join(
                        entities.get(
                            "industries",
                            [],
                        ),
                    ),
                    "question": query,
                },
            )
            return self._parse_plan_output(raw)
        except Exception:
            logger.warning(
                "LLM planning failed for: {}",
                query[:60],
            )
            return []

    @staticmethod
    def _parse_plan_output(
        raw: str,
    ) -> list[PlannedAction]:
        """Extract JSON tool calls from LLM output."""
        match = re.search(
            r"\[.*\]",
            raw,
            re.DOTALL,
        )
        if not match:
            return []

        try:
            items = json.loads(match.group())
        except json.JSONDecodeError:
            return []

        actions: list[PlannedAction] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            tool = item.get("tool", "")
            if not tool:
                continue
            actions.append(
                PlannedAction(
                    tool=tool,
                    params=item.get("params", {}),
                    rationale=item.get(
                        "rationale",
                        "",
                    ),
                ),
            )
        return actions
