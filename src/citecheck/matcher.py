"""Thematic and semantic matching for citations."""

import os
from dataclasses import dataclass
from typing import List

from .parser import Citation, Paper, Reference


@dataclass
class MatchResult:
    ref_index: int
    score: float = 0.0
    reason: str = ""


class ThematicMatcher:
    """Evaluate thematic relevance between paper and cited works."""

    EVALUATION_PROMPT = """\
You are an academic peer reviewer. Evaluate the thematic relevance of a cited paper to the citing paper.

【Citing Paper】
Title: {paper_title}
Abstract: {paper_abstract}
Keywords: {paper_keywords}

【Cited Paper】
Title: {cited_title}
Abstract: {cited_abstract}
Venue: {cited_venue}

【Scoring Rubric】
- 1.0: Directly essential (core dataset, benchmark, or backbone model)
- 0.8: Strongly relevant (same subfield, directly supports methodology)
- 0.5: Moderately relevant (same broad domain, background/context)
- 0.2: Weakly relevant (tangential connection)
- 0.0: Unrelated

Output ONLY a JSON object: {{"score": float, "reason": "one sentence"}}
"""

    def evaluate(self, paper: Paper) -> List[MatchResult]:
        """Evaluate thematic relevance for all references."""
        results = []
        # Heuristic scoring without LLM
        for ref in paper.references:
            score, reason = self._heuristic_score(paper, ref)
            results.append(MatchResult(ref.index, score, reason))
        return results

    def _heuristic_score(self, paper: Paper, ref: Reference) -> tuple:
        """Simple heuristic for thematic scoring."""
        title_lower = (ref.title or "").lower()
        paper_title = (paper.title or "").lower()

        # Directly essential keywords
        essential = ["bioasq", "biomistral", "dataset", "corpus", "benchmark"]
        for kw in essential:
            if kw in title_lower:
                if kw in paper_title or kw in (paper.abstract or "").lower():
                    return 1.0, f"Directly essential: {ref.title[:50]}"

        # Domain relevance
        bio_keywords = ["biomedical", "bio", "medical", "clinical", "health"]
        bio_match = sum(1 for kw in bio_keywords if kw in title_lower)
        if bio_match >= 2:
            return 0.8, f"Strong biomedical relevance"
        if bio_match == 1:
            return 0.6, f"Moderate biomedical relevance"

        # Method relevance
        method_keywords = ["prompt", "verification", "aggregation", "reasoning", "language model"]
        method_match = sum(1 for kw in method_keywords if kw in title_lower)
        if method_match >= 2:
            return 0.7, f"Methodologically relevant"
        if method_match == 1:
            return 0.5, f"Partially relevant"

        return 0.4, f"Background/general reference"


class SemanticMatcher:
    """Evaluate semantic accuracy of in-text citations against source content."""

    EVALUATION_PROMPT = """\
You are a text semantic matching expert. Compute the semantic match between two text passages.

【Scoring】
- 1.0: Semantically identical
- 0.8: Highly similar (core meaning matches)
- 0.5: Partially related (same topic, different specifics)
- 0.2: Weakly related
- 0.0: Unrelated

Text A (citing text): {citing_text}
Text B (cited paper title): {cited_title}

Output ONLY: SCORE | ONE_SENTENCE_REASON
"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def evaluate(self, paper: Paper) -> List[MatchResult]:
        """Evaluate semantic match for each unique citation."""
        results = []
        ref_map = {r.index: r for r in paper.references}

        for cite in paper.citations:
            for idx in cite.ref_indices:
                ref = ref_map.get(idx)
                if not ref:
                    continue
                score, reason = self._heuristic_semantic(cite, ref)
                results.append(MatchResult(idx, score, reason))
        return results

    def _heuristic_semantic(self, cite: Citation, ref: Reference) -> tuple:
        """Simple heuristic semantic matching."""
        context = (cite.context_before + " " + cite.context_after).lower()
        title = (ref.title or "").lower()

        # Direct mention
        if any(word in context for word in title.split()[:5]):
            return 0.9, "Title keywords directly mentioned in context"

        # Topic overlap
        overlap = sum(1 for w in title.split() if len(w) > 4 and w in context)
        if overlap >= 3:
            return 0.85, f"Strong lexical overlap ({overlap} keywords)"
        if overlap >= 1:
            return 0.7, f"Partial lexical overlap ({overlap} keywords)"

        # Check for named citations
        if ref.authors:
            first_author = ref.authors.split(",")[0].split()[-1].lower()
            if first_author in context:
                return 0.8, f"Author '{first_author}' mentioned in context"

        return 0.6, "Weak semantic match; verify claim accuracy manually"
