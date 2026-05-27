"""Citation verification via Crossref, Semantic Scholar, and WebSearch."""

import time
import urllib.parse
from dataclasses import dataclass, field
from typing import List, Optional

from citecheck.models import Reference


@dataclass
class QueryResult:
    ref_index: int
    found: bool = False
    matched_title: str = ""
    matched_year: str = ""
    matched_venue: str = ""
    matched_doi: str = ""
    score: float = 0.0
    source: str = ""
    message: str = ""
    warnings: List[str] = field(default_factory=list)


class CitationVerifier:
    """Verify if cited papers exist via academic APIs."""

    def __init__(self, skip_online: bool = False):
        self.skip_online = skip_online
        self.session = None
        try:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "CiteCheck/0.1.0 (mailto:citecheck@example.com)"
            })
        except ImportError:
            pass

    def check_format(self, refs: List[Reference]) -> List[Reference]:
        """Run format checks on all references."""
        # Issues are already populated during parsing
        return refs

    def verify_queryability(self, refs: List[Reference]) -> List[QueryResult]:
        """Verify each reference exists via online queries."""
        if self.skip_online or not self.session:
            return []

        results = []
        for ref in refs:
            result = self._query_all_sources(ref)
            results.append(result)
            time.sleep(0.5)  # Be polite to APIs
        return results

    def _query_all_sources(self, ref: Reference) -> QueryResult:
        result = QueryResult(ref_index=ref.index)

        # 1. Try Crossref
        crossref = self._query_crossref(ref)
        if crossref and crossref.found:
            return crossref

        # 2. Try Semantic Scholar
        ss = self._query_semantic_scholar(ref)
        if ss and ss.found:
            return ss

        # 3. Fallback: not found
        result.message = "Not found via Crossref or Semantic Scholar"
        return result

    def _query_crossref(self, ref: Reference) -> Optional[QueryResult]:
        if not ref.title:
            return None
        try:
            encoded = urllib.parse.quote(ref.title)
            url = f"https://api.crossref.org/works?query.title={encoded}&rows=3&mailto=citecheck@example.com"
            resp = self.session.get(url, timeout=15)
            data = resp.json()
            items = data.get("message", {}).get("items", [])
            if items:
                item = items[0]
                result = QueryResult(
                    ref_index=ref.index,
                    found=True,
                    source="Crossref",
                    score=item.get("score", 0),
                )
                result.matched_title = (item.get("title") or [""])[0]
                result.matched_doi = item.get("DOI", "")
                result.matched_venue = (item.get("container-title") or [""])[0]

                # Extract year
                pub = item.get("published-print", {}) or item.get("published-online", {})
                parts = pub.get("date-parts", [[""]])[0]
                result.matched_year = str(parts[0]) if parts else ""

                # Compare with reference
                if ref.year and result.matched_year and ref.year not in result.matched_year:
                    result.warnings.append(f"Year mismatch: ref={ref.year}, found={result.matched_year}")
                return result
        except Exception as e:
            return QueryResult(ref_index=ref.index, source="Crossref", message=str(e))
        return None

    def _query_semantic_scholar(self, ref: Reference) -> Optional[QueryResult]:
        if not ref.title:
            return None
        try:
            encoded = urllib.parse.quote(ref.title)
            fields = "title,authors,year,abstract,fieldsOfStudy,citationCount,paperId"
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded}&fields={fields}&limit=3"
            resp = self.session.get(url, timeout=15)
            data = resp.json()
            items = data.get("data", [])
            if items:
                item = items[0]
                result = QueryResult(
                    ref_index=ref.index,
                    found=True,
                    source="SemanticScholar",
                    matched_title=item.get("title", ""),
                    matched_year=str(item.get("year", "")),
                )
                if ref.year and result.matched_year and ref.year != result.matched_year:
                    result.warnings.append(f"Year mismatch: ref={ref.year}, found={result.matched_year}")
                return result
        except Exception as e:
            return QueryResult(ref_index=ref.index, source="SemanticScholar", message=str(e))
        return None
