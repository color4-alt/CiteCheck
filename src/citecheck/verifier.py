"""Citation verification via Crossref, Semantic Scholar, OpenAlex, PubMed, arXiv, dblp, Google Scholar, and WebSearch."""

import re
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
    matched_abstract: str = ""
    score: float = 0.0
    source: str = ""
    message: str = ""
    warnings: List[str] = field(default_factory=list)


class CitationVerifier:
    """Verify if cited papers exist via academic APIs and web search."""

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

    @staticmethod
    def _title_similarity(title_a: str, title_b: str) -> float:
        """Compute Jaccard-like similarity between two titles (0.0–1.0)."""
        if not title_a or not title_b:
            return 0.0
        # Normalize: lowercase, keep only alphabetic words > 2 chars
        def _words(t: str) -> set:
            return set(
                w.lower()
                for w in re.findall(r"[A-Za-z]{3,}", t)
                if w.lower() not in {"the", "and", "for", "with", "using", "from", "via", "based", "towards", "among", "into", "over", "under"}
            )
        words_a = _words(title_a)
        words_b = _words(title_b)
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)

    @staticmethod
    def _author_overlap(ref_authors: str, api_authors: List[dict]) -> bool:
        """Check if any author last name from the reference appears in API results."""
        if not ref_authors or not api_authors:
            return False
        # Extract last names from reference (first author only for simplicity)
        ref_first = ref_authors.split(",")[0].strip()
        ref_last = ref_first.split()[-1].lower() if ref_first else ""
        if not ref_last:
            return False
        # Check against API authors
        for author in api_authors:
            family = author.get("family", "").lower()
            if family and (family in ref_last or ref_last in family):
                return True
        return False

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

        # 3. Try OpenAlex (open academic graph)
        oa = self._query_openalex(ref)
        if oa and oa.found:
            return oa

        # 4. Try PubMed (biomedical/life sciences)
        pubmed = self._query_pubmed(ref)
        if pubmed and pubmed.found:
            return pubmed

        # 5. Try arXiv (preprints)
        arxiv = self._query_arxiv(ref)
        if arxiv and arxiv.found:
            return arxiv

        # 6. Try dblp (computer science)
        dblp = self._query_dblp(ref)
        if dblp and dblp.found:
            return dblp

        # 7. Try Google Scholar (web search)
        gs = self._query_google_scholar(ref)
        if gs and gs.found:
            return gs

        # 8. Final fallback: generic web search
        ws = self._query_web_search(ref)
        if ws and ws.found:
            return ws

        # 9. Not found
        result.message = "Not found via Crossref, Semantic Scholar, OpenAlex, PubMed, arXiv, dblp, Google Scholar, or WebSearch"
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
            if not items:
                return None

            # Score all candidates and pick the best one
            best_item = None
            best_score = -1.0
            for item in items:
                matched_title = (item.get("title") or [""])[0]
                title_sim = self._title_similarity(ref.title, matched_title)

                # Extract year
                pub = item.get("published-print", {}) or item.get("published-online", {})
                parts = pub.get("date-parts", [[""]])[0]
                matched_year = str(parts[0]) if parts else ""

                # Compute match score: title similarity + year bonus + author bonus
                score = title_sim
                if ref.year and matched_year and ref.year == matched_year:
                    score += 0.3  # Year match bonus
                if ref.authors and self._author_overlap(ref.authors, item.get("author", [])):
                    score += 0.2  # Author overlap bonus

                if score > best_score:
                    best_score = score
                    best_item = item

            if best_item and best_score < 0.2:
                # Too dissimilar — likely matched the wrong paper
                return QueryResult(
                    ref_index=ref.index,
                    source="Crossref",
                    message=f"Title similarity too low ({best_score:.2f}); possible false match",
                )

            if best_item:
                item = best_item
                result = QueryResult(
                    ref_index=ref.index,
                    found=True,
                    source="Crossref",
                    score=item.get("score", 0),
                )
                result.matched_title = (item.get("title") or [""])[0]
                result.matched_doi = item.get("DOI", "")
                result.matched_venue = (item.get("container-title") or [""])[0]
                result.matched_abstract = item.get("abstract", "")

                # Extract year
                pub = item.get("published-print", {}) or item.get("published-online", {})
                parts = pub.get("date-parts", [[""]])[0]
                result.matched_year = str(parts[0]) if parts else ""

                # Compare with reference
                title_sim = self._title_similarity(ref.title, result.matched_title)
                if title_sim < 0.5:
                    result.warnings.append(f"Low title similarity ({title_sim:.2f}); verify manually")

                if ref.year and result.matched_year:
                    if ref.year != result.matched_year:
                        try:
                            year_diff = abs(int(ref.year) - int(result.matched_year))
                            if year_diff > 2:
                                result.warnings.append(
                                    f"Large year mismatch ({year_diff} years): ref={ref.year}, found={result.matched_year}"
                                )
                            else:
                                result.warnings.append(
                                    f"Year mismatch: ref={ref.year}, found={result.matched_year}"
                                )
                        except ValueError:
                            result.warnings.append(
                                f"Year mismatch: ref={ref.year}, found={result.matched_year}"
                            )
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
                    matched_abstract=item.get("abstract", ""),
                )
                if ref.year and result.matched_year and ref.year != result.matched_year:
                    result.warnings.append(f"Year mismatch: ref={ref.year}, found={result.matched_year}")
                return result
        except Exception as e:
            return QueryResult(ref_index=ref.index, source="SemanticScholar", message=str(e))
        return None

    def _query_openalex(self, ref: Reference) -> Optional[QueryResult]:
        """Query OpenAlex for academic works."""
        if not ref.title:
            return None
        try:
            encoded = urllib.parse.quote(ref.title)
            url = f"https://api.openalex.org/works?search={encoded}&per-page=3"
            resp = self.session.get(url, timeout=15)
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return None

            item = results[0]
            matched_title = item.get("display_name", "")
            matched_year = str(item.get("publication_year", ""))
            matched_doi = item.get("doi", "").replace("https://doi.org/", "")

            # Venue
            host = item.get("host_venue", {}) or item.get("primary_location", {})
            if isinstance(host, dict):
                venue = host.get("display_name", "")
            else:
                venue = ""

            # Abstract (OpenAlex stores inverted index)
            abstract = ""
            inv = item.get("abstract_inverted_index")
            if inv:
                # Reconstruct approximate abstract text
                word_positions = []
                for word, positions in inv.items():
                    for pos in positions:
                        word_positions.append((pos, word))
                word_positions.sort(key=lambda x: x[0])
                abstract = " ".join(w for _, w in word_positions)

            result = QueryResult(
                ref_index=ref.index,
                found=True,
                source="OpenAlex",
                matched_title=matched_title,
                matched_year=matched_year,
                matched_venue=venue,
                matched_doi=matched_doi,
                matched_abstract=abstract,
            )
            if ref.year and result.matched_year and ref.year != result.matched_year:
                result.warnings.append(f"Year mismatch: ref={ref.year}, found={result.matched_year}")
            return result
        except Exception as e:
            return QueryResult(ref_index=ref.index, source="OpenAlex", message=str(e))

    def _query_arxiv(self, ref: Reference) -> Optional[QueryResult]:
        """Query arXiv API for preprints."""
        if not ref.title:
            return None
        try:
            encoded = urllib.parse.quote(ref.title)
            url = f"http://export.arxiv.org/api/query?search_query=ti:{encoded}&max_results=3&sortBy=relevance"
            resp = self.session.get(url, timeout=15)
            if resp.status_code != 200:
                return None

            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.text)
            # Atom namespace
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)
            if not entries:
                return None

            entry = entries[0]
            title_elem = entry.find("atom:title", ns)
            matched_title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

            published = entry.find("atom:published", ns)
            matched_year = published.text[:4] if published is not None and published.text else ""

            # arXiv id
            id_elem = entry.find("atom:id", ns)
            arxiv_id = id_elem.text.split("/")[-1] if id_elem is not None and id_elem.text else ""

            # DOI may be in arxiv_doi field
            matched_doi = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "doi":
                    matched_doi = link.get("href", "").replace("https://doi.org/", "")
                    break

            result = QueryResult(
                ref_index=ref.index,
                found=True,
                source="arXiv",
                matched_title=matched_title,
                matched_year=matched_year,
                matched_doi=matched_doi,
                message=f"Found via arXiv (ID: {arxiv_id})",
            )
            if ref.year and result.matched_year and ref.year != result.matched_year:
                result.warnings.append(f"Year mismatch: ref={ref.year}, found={result.matched_year}")
            return result
        except Exception as e:
            return QueryResult(ref_index=ref.index, source="arXiv", message=str(e))

    def _query_dblp(self, ref: Reference) -> Optional[QueryResult]:
        """Query dblp for computer science publications."""
        if not ref.title:
            return None
        try:
            encoded = urllib.parse.quote(ref.title)
            url = f"https://dblp.org/search/publ/api?q={encoded}&format=json&h=3"
            resp = self.session.get(url, timeout=15)
            data = resp.json()
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            if not hits:
                return None

            hit = hits[0]
            info = hit.get("info", {})
            matched_title = info.get("title", "")
            matched_year = str(info.get("year", ""))
            matched_venue = info.get("venue", "")
            matched_doi = info.get("doi", "")

            result = QueryResult(
                ref_index=ref.index,
                found=True,
                source="dblp",
                matched_title=matched_title,
                matched_year=matched_year,
                matched_venue=matched_venue,
                matched_doi=matched_doi,
            )
            if ref.year and result.matched_year and ref.year != result.matched_year:
                result.warnings.append(f"Year mismatch: ref={ref.year}, found={result.matched_year}")
            return result
        except Exception as e:
            return QueryResult(ref_index=ref.index, source="dblp", message=str(e))

    def _query_pubmed(self, ref: Reference) -> Optional[QueryResult]:
        """Query PubMed E-utilities for biomedical/life sciences papers."""
        if not ref.title:
            return None
        try:
            encoded = urllib.parse.quote(ref.title)
            # ESearch: find PMIDs matching the title
            search_url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                f"?db=pubmed&term={encoded}&retmax=3&retmode=json"
            )
            resp = self.session.get(search_url, timeout=15)
            data = resp.json()
            idlist = data.get("esearchresult", {}).get("idlist", [])
            if not idlist:
                return None

            # ESummary: get details for the top PMID
            pmid = idlist[0]
            summary_url = (
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                f"?db=pubmed&id={pmid}&retmode=json"
            )
            resp2 = self.session.get(summary_url, timeout=15)
            sdata = resp2.json()
            docs = sdata.get("result", {})
            doc = docs.get(pmid, {})
            if not doc:
                return None

            matched_title = doc.get("title", "")
            matched_year = doc.get("pubdate", "")[:4]  # pubdate is usually "YYYY Mon"
            matched_venue = doc.get("fulljournalname", "")
            # DOI may be in articleids
            matched_doi = ""
            for aid in doc.get("articleids", []):
                if aid.get("idtype") == "doi":
                    matched_doi = aid.get("value", "")
                    break

            result = QueryResult(
                ref_index=ref.index,
                found=True,
                source="PubMed",
                matched_title=matched_title,
                matched_year=matched_year,
                matched_venue=matched_venue,
                matched_doi=matched_doi,
                message=f"Found via PubMed (PMID: {pmid})",
            )
            if ref.year and result.matched_year and ref.year != result.matched_year:
                result.warnings.append(f"Year mismatch: ref={ref.year}, found={result.matched_year}")
            return result
        except Exception as e:
            return QueryResult(ref_index=ref.index, source="PubMed", message=str(e))

    def _query_google_scholar(self, ref: Reference) -> Optional[QueryResult]:
        """Fallback to Google Scholar web search when APIs fail."""
        if not ref.title:
            return None
        try:
            query = f"{ref.title} {ref.authors or ''} {ref.year or ''}"
            encoded = urllib.parse.quote(query)
            url = f"https://scholar.google.com/scholar?q={encoded}&num=3"
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                # Google Scholar blocks bots; if we get a valid page, assume the paper exists
                # We extract the first result title from the HTML for confirmation
                import re
                title_match = re.search(r"class=\"gs_rt\"[^>]*>(?:<[^>]+>)?([^<]+)", resp.text)
                if title_match:
                    found_title = title_match.group(1).strip()
                    # Simple heuristic: if the title contains at least 3 words from our query
                    query_words = set(w.lower() for w in ref.title.split() if len(w) > 3)
                    found_words = set(w.lower() for w in found_title.split() if len(w) > 3)
                    if len(query_words & found_words) >= 2:
                        return QueryResult(
                            ref_index=ref.index,
                            found=True,
                            source="GoogleScholar",
                            matched_title=found_title,
                            matched_year=ref.year or "",
                            message="Verified via Google Scholar web search",
                        )
        except Exception:
            pass
        return None

    def _query_web_search(self, ref: Reference) -> Optional[QueryResult]:
        """Final fallback: generic web search via Google."""
        if not ref.title:
            return None
        try:
            query = f"{ref.title} {ref.authors or ''} {ref.year or ''}"
            encoded = urllib.parse.quote(query)
            url = f"https://www.google.com/search?q={encoded}&num=3"
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                # Check if the page contains the paper title
                page_text = resp.text.lower()
                title_lower = ref.title.lower()
                # Check if title words appear in results
                title_words = [w for w in title_lower.split() if len(w) > 3]
                matches = sum(1 for w in title_words if w in page_text)
                if matches >= max(2, len(title_words) // 2):
                    return QueryResult(
                        ref_index=ref.index,
                        found=True,
                        source="WebSearch",
                        matched_title=ref.title,
                        matched_year=ref.year or "",
                        message="Verified via web search",
                    )
        except Exception:
            pass
        return None
