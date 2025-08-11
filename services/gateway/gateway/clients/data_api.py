"""HTTP client for the backend data API."""

from __future__ import annotations

from typing import Any

import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)


class DataServiceClient:
    """Wraps HTTP calls to the backend data service."""

    def __init__(
        self,
        base_url: str,
        token: str = "",
        timeout_seconds: int = 30,
    ) -> None:
        headers: dict[str, str] = {
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout_seconds,
        )
        self._base_url = base_url
        self._tool_map: dict[
            str,
            Any,
        ] = self._build_tool_map()

    def _build_tool_map(
        self,
    ) -> dict[str, Any]:
        """Internal registry of tool-name to method."""
        return {
            "query_team": self.query_team,
            "query_team_analysis": (self.query_team_analysis),
            "query_portfolio": self.query_portfolio,
            "query_portfolio_analysis": (self.query_portfolio_analysis),
            "query_verticals": self.query_verticals,
            "query_engagements": (self.query_engagements),
            "query_web_content": (self.query_web_content),
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=0.5,
            max=5,
        ),
        reraise=True,
    )
    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send GET with retries."""
        resp = self._client.get(
            path,
            params=params,
        )
        resp.raise_for_status()
        return resp.json()  # type: ignore[no-any-return]

    def ping(self) -> dict[str, Any]:
        """Health-check the backend."""
        return self._get("/health")

    def is_reachable(self) -> bool:
        """Return True if the backend responds."""
        try:
            self.ping()
            return True
        except Exception:
            logger.warning(
                "Backend at {} unreachable",
                self._base_url,
            )
            return False

    def download_corpus_archive(self) -> bytes:
        """Fetch the document corpus ZIP."""
        resp = self._client.get(
            "/api/corpus/download",
        )
        resp.raise_for_status()
        return resp.content

    def query_team(
        self,
        name: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        """Retrieve team member information."""
        params = {"name": name} if name else {}
        return self._get(
            "/api/team",
            params=params,
        )

    def query_team_analysis(
        self,
        name: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        """Retrieve team analysis data."""
        params = {"name": name} if name else {}
        return self._get(
            "/api/team/analysis",
            params=params,
        )

    def query_portfolio(
        self,
        company: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        """Retrieve portfolio company data."""
        params = {"company": company} if company else {}
        return self._get(
            "/api/portfolio",
            params=params,
        )

    def query_portfolio_analysis(
        self,
        company: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        """Retrieve portfolio analysis data."""
        params = {"company": company} if company else {}
        return self._get(
            "/api/portfolio/analysis",
            params=params,
        )

    def query_verticals(
        self,
        sector: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        """Retrieve industry vertical data."""
        params = {"sector": sector} if sector else {}
        return self._get(
            "/api/verticals",
            params=params,
        )

    def query_engagements(
        self,
        name: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        """Retrieve engagement records."""
        params = {"name": name} if name else {}
        return self._get(
            "/api/engagements",
            params=params,
        )

    def query_web_content(
        self,
        url: str = "",
        **_: Any,
    ) -> dict[str, Any]:
        """Fetch web page content via backend."""
        return self._get(
            "/api/web",
            params={"url": url},
        )

    def dispatch_tool(
        self,
        tool_name: str,
        **params: Any,
    ) -> dict[str, Any]:
        """Route a tool call to the right method."""
        handler = self._tool_map.get(tool_name)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return handler(**params)  # type: ignore[no-any-return]

    def registered_tool_names(self) -> list[str]:
        """List all available tool names."""
        return list(self._tool_map.keys())

    def close(self) -> None:
        """Shut down the HTTP client."""
        self._client.close()
