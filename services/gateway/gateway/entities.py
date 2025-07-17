"""Named-entity extraction from user queries."""

from __future__ import annotations

import re

_PERSON_PATTERN = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b",
)

_ORG_PATTERN = re.compile(
    r"\b([A-Z][A-Za-z]*(?:\s+(?:Inc|Corp|LLC|Ltd|Group"
    r"|Partners|Capital|Holdings|Ventures|Fund|Bank"
    r"|Technologies|Solutions|Labs|Co)\.?))\b",
)

_INDUSTRY_KEYWORDS: set[str] = {
    "healthcare",
    "finance",
    "technology",
    "energy",
    "manufacturing",
    "retail",
    "telecommunications",
    "real estate",
    "education",
    "automotive",
    "pharmaceuticals",
    "media",
    "insurance",
    "logistics",
    "agriculture",
    "aerospace",
    "defense",
    "biotech",
    "fintech",
    "saas",
    "consulting",
}

_URL_PATTERN = re.compile(
    r"https?://[^\s<>\"']+",
)


def extract_named_entities(
    text: str,
) -> dict[str, list[str]]:
    """Pull people, orgs, industries, and URLs."""
    lower_text = text.lower()

    people = _dedupe(
        _PERSON_PATTERN.findall(text),
    )
    organisations = _dedupe(
        _ORG_PATTERN.findall(text),
    )
    industries = [kw for kw in _INDUSTRY_KEYWORDS if kw in lower_text]
    links = _dedupe(
        _URL_PATTERN.findall(text),
    )

    return {
        "people": people,
        "organisations": organisations,
        "industries": sorted(industries),
        "links": links,
    }


def _dedupe(items: list[str]) -> list[str]:
    """Remove duplicates while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
