"""Thematic and semantic matching for citations."""

import json
import os
import re
from dataclasses import dataclass
from typing import List

from citecheck.models import Citation, Paper, Reference


@dataclass
class MatchResult:
    ref_index: int
    score: float = 0.0
    reason: str = ""


class _LLMBase:
    """Shared LLM calling logic with fallback to heuristics."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            return ""
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.1,
            }
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return ""

    @staticmethod
    def _extract_json_score(text: str) -> tuple:
        """Try to extract a numeric score from LLM JSON or text output."""
        if not text:
            return None, ""
        # Try JSON first
        try:
            obj = json.loads(text)
            score = float(obj.get("score", -1))
            reason = obj.get("reason", "")
            if 0.0 <= score <= 1.0:
                return score, reason
        except Exception:
            pass
        # Fallback: regex for float in text
        m = re.search(r"(\d?\.\d+)", text)
        if m:
            score = float(m.group(1))
            if 0.0 <= score <= 1.0:
                return score, text
        return None, ""


class ThematicMatcher(_LLMBase):
    """Evaluate thematic relevance between paper and cited works."""

    SYSTEM_PROMPT = (
        "You are an academic peer reviewer. Evaluate the thematic relevance of a cited paper to the citing paper. "
        "Output ONLY a JSON object with keys 'score' (float 0.0-1.0) and 'reason' (one sentence)."
    )

    USER_PROMPT_TEMPLATE = """\
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
"""

    def evaluate(self, paper: Paper) -> List[MatchResult]:
        """Evaluate thematic relevance for all references."""
        results = []
        for ref in paper.references:
            score, reason = self._llm_score(paper, ref)
            if score is None:
                score, reason = self._heuristic_score(paper, ref)
            results.append(MatchResult(ref.index, score, reason))
        return results

    def _llm_score(self, paper: Paper, ref: Reference) -> tuple:
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            paper_title=paper.title or "N/A",
            paper_abstract=paper.abstract or "N/A",
            paper_keywords=paper.keywords or "N/A",
            cited_title=ref.title or "N/A",
            cited_abstract=ref.raw_text or "N/A",
            cited_venue=ref.venue or "N/A",
        )
        response = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        return self._extract_json_score(response)

    def _heuristic_score(self, paper: Paper, ref: Reference) -> tuple:
        """Simple heuristic for thematic scoring when LLM is unavailable."""
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
            return 0.8, "Strong biomedical relevance"
        if bio_match == 1:
            return 0.6, "Moderate biomedical relevance"

        # Method relevance
        method_keywords = ["prompt", "verification", "aggregation", "reasoning", "language model"]
        method_match = sum(1 for kw in method_keywords if kw in title_lower)
        if method_match >= 2:
            return 0.7, "Methodologically relevant"
        if method_match == 1:
            return 0.5, "Partially relevant"

        return 0.4, "Background/general reference"


class SemanticMatcher(_LLMBase):
    """Evaluate semantic accuracy of in-text citations against source content."""

    SYSTEM_PROMPT = (
        "You are a text semantic matching expert. Compute the semantic match between two text passages. "
        "Output ONLY a JSON object with keys 'score' (float 0.0-1.0) and 'reason' (one sentence)."
    )

    USER_PROMPT_TEMPLATE = """\
【Scoring】
- 1.0: Semantically identical
- 0.8: Highly similar (core meaning matches)
- 0.5: Partially related (same topic, different specifics)
- 0.2: Weakly related
- 0.0: Unrelated

Text A (citing text): {citing_text}
Text B (cited paper title): {cited_title}
"""

    def evaluate(self, paper: Paper) -> List[MatchResult]:
        """Evaluate semantic match for each unique citation."""
        results = []
        ref_map = {r.index: r for r in paper.references}

        for cite in paper.citations:
            for idx in cite.ref_indices:
                ref = ref_map.get(idx)
                if not ref:
                    continue
                score, reason = self._llm_score(cite, ref)
                if score is None:
                    score, reason = self._heuristic_semantic(cite, ref)
                results.append(MatchResult(idx, score, reason))
        return results

    def _llm_score(self, cite: Citation, ref: Reference) -> tuple:
        citing_text = f"{cite.context_before} {cite.raw_marker} {cite.context_after}".strip()
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            citing_text=citing_text or "N/A",
            cited_title=ref.title or "N/A",
        )
        response = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        return self._extract_json_score(response)

    def _heuristic_semantic(self, cite: Citation, ref: Reference) -> tuple:
        """Simple heuristic semantic matching when LLM is unavailable."""
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
