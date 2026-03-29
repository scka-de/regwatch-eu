"""EUR-Lex SPARQL source for regulatory changes."""

from __future__ import annotations

import logging
from datetime import date

import httpx

from regwatch.models import RawChange
from regwatch.regulations.base import Regulation

logger = logging.getLogger(__name__)

SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
SPARQL_RESULT_LIMIT = 200


def _escape_sparql_string(s: str) -> str:
    """Escape special characters for SPARQL string literals."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


class EurLexSource:
    id: str = "eurlex"
    name: str = "EUR-Lex"

    def fetch(self, since: date, regulations: list[Regulation]) -> list[RawChange]:
        """Fetch regulatory changes from EUR-Lex SPARQL endpoint."""
        if not regulations:
            return []
        query = self._build_query(since, regulations)
        if not query:
            return []
        try:
            response = httpx.post(
                SPARQL_ENDPOINT,
                data={"query": query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=90.0,
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except httpx.TimeoutException:
            logger.warning("EUR-Lex SPARQL request timed out")
            raise
        except httpx.HTTPStatusError as e:
            logger.warning("EUR-Lex SPARQL HTTP error: %s", e.response.status_code)
            raise

    def _build_query(self, since: date, regulations: list[Regulation]) -> str:
        """Build a SPARQL query filtering by date and regulation keywords."""
        all_keywords: list[str] = []
        for reg in regulations:
            all_keywords.extend(reg.keywords)

        if not all_keywords:
            return ""

        # Build FILTER clause matching any keyword in title (case-insensitive)
        keyword_filters = " || ".join(
            f'CONTAINS(LCASE(?title), "{_escape_sparql_string(kw.lower())}")'
            for kw in all_keywords
        )

        return f"""
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?cellarURI ?title ?date ?celex WHERE {{
    ?cellarURI cdm:work_date_document ?date .
    ?expression cdm:expression_belongs_to_work ?cellarURI .
    ?expression cdm:expression_uses_language
        <http://publications.europa.eu/resource/authority/language/ENG> .
    ?expression cdm:expression_title ?title .
    OPTIONAL {{ ?cellarURI cdm:resource_legal_id_celex ?celex . }}
    FILTER(?date > "{since.isoformat()}"^^xsd:date)
    FILTER({keyword_filters})
}}
ORDER BY DESC(?date)
LIMIT {SPARQL_RESULT_LIMIT}
"""

    def _parse_response(self, data: dict) -> list[RawChange]:
        """Parse SPARQL JSON response into RawChange list."""
        results: list[RawChange] = []
        for binding in data.get("results", {}).get("bindings", []):
            url = binding.get("cellarURI", {}).get("value", "")
            title = binding.get("title", {}).get("value", "")
            date_str = binding.get("date", {}).get("value", "")
            celex = binding.get("celex", {}).get("value", "")

            if not url or not title or not date_str:
                continue

            parsed_date = date.fromisoformat(date_str[:10])
            results.append(
                RawChange(
                    title=title,
                    date=parsed_date,
                    url=url,
                    source="eurlex",
                    celex_id=celex,
                )
            )
        return results
