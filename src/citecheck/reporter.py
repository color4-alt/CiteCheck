"""Markdown report generator for citation checks."""

from datetime import datetime
from typing import List

from citecheck.matcher import MatchResult
from citecheck.models import Citation, Paper, Reference
from citecheck.verifier import QueryResult


class ReportGenerator:
    """Generate a structured Markdown report."""

    def generate(
        self,
        paper: Paper,
        format_results: List[Reference],
        query_results: List[QueryResult],
        thematic_results: List[MatchResult],
        semantic_results: List[MatchResult],
    ) -> str:
        lines = []

        # Header
        lines.append("# Citation Check Report\n")
        lines.append(f"**Paper**: {paper.title or 'Unknown'}  ")
        lines.append(f"**Check Date**: {datetime.now().strftime('%Y-%m-%d')}  ")
        lines.append(f"**Source Type**: {paper.source_type}  ")
        lines.append(f"**Total References**: {len(paper.references)}  ")
        lines.append(f"**Citations in Text**: {len(paper.citations)}\n")

        # Summary
        lines.append("## Summary\n")
        issue_count = sum(1 for r in format_results if r.issues)
        found_count = sum(1 for r in query_results if r.found)
        avg_thematic = (
            sum(r.score for r in thematic_results) / len(thematic_results)
            if thematic_results else 0
        )
        avg_semantic = (
            sum(r.score for r in semantic_results) / len(semantic_results)
            if semantic_results else 0
        )

        lines.append("| Metric | Result |")
        lines.append("|--------|--------|")
        lines.append(f"| Total References | {len(paper.references)} |")
        lines.append(f"| Format Issues | {issue_count} |")
        lines.append(f"| Online Verified | {found_count}/{len(query_results) if query_results else 'N/A'} |")
        lines.append(f"| Avg Thematic Relevance | {avg_thematic:.2f} |")
        lines.append(f"| Avg Semantic Accuracy | {avg_semantic:.2f} |")
        lines.append("")

        # Detailed table
        lines.append("## Detailed Results\n")
        lines.append("| No. | Title | Format | Queryable | Thematic | Semantic | Notes |")
        lines.append("|-----|-------|--------|-----------|----------|----------|-------|")

        ref_map = {r.index: r for r in paper.references}
        query_map = {r.ref_index: r for r in query_results}
        thematic_map = {r.ref_index: r for r in thematic_results}
        semantic_map = {r.ref_index: r for r in semantic_results}

        for ref in paper.references:
            q = query_map.get(ref.index)
            t = thematic_map.get(ref.index)
            s = semantic_map.get(ref.index)

            fmt = "⚠️" if ref.issues else "✅"
            qry = "✅" if (q and q.found) else ("❌" if q else "—")
            thm = f"{t.score:.2f}" if t else "—"
            sem = f"{s.score:.2f}" if s else "—"
            notes = "; ".join(ref.issues[:2]) if ref.issues else "OK"
            if q and q.warnings:
                notes += "; " + "; ".join(q.warnings[:1])

            title_short = (ref.title or ref.bib_key or "Untitled")[:45]
            lines.append(f"| {ref.index} | {title_short} | {fmt} | {qry} | {thm} | {sem} | {notes} |")
        lines.append("")

        # Format check details
        lines.append("## 1. Format Check Details\n")
        critical = [r for r in format_results if r.issues]
        if critical:
            for ref in critical:
                lines.append(f"### [{ref.index}] {ref.title or ref.bib_key}")
                for issue in ref.issues:
                    lines.append(f"- ⚠️ {issue}")
                lines.append("")
        else:
            lines.append("All references pass basic format checks. ✅\n")

        # Queryability
        if query_results:
            lines.append("## 2. Queryability Verification\n")
            for q in query_results:
                ref = ref_map.get(q.ref_index)
                if q.found:
                    lines.append(
                        f"- **[{q.ref_index}]** ✅ Found via {q.source}: "
                        f"\"{q.matched_title[:50]}...\" ({q.matched_year})"
                    )
                else:
                    lines.append(f"- **[{q.ref_index}]** ❌ {q.message}")
            lines.append("")

        # Thematic relevance
        if thematic_results:
            lines.append("## 3. Thematic Relevance\n")
            lines.append("| No. | Score | Reason |")
            lines.append("|-----|-------|--------|")
            for t in sorted(thematic_results, key=lambda x: x.ref_index):
                lines.append(f"| {t.ref_index} | {t.score:.2f} | {t.reason} |")
            lines.append("")

        # Semantic accuracy
        if semantic_results:
            lines.append("## 4. Semantic Accuracy\n")
            lines.append("| Citation | Score | Reason |")
            lines.append("|----------|-------|--------|")
            for s in sorted(semantic_results, key=lambda x: x.ref_index):
                lines.append(f"| [{s.ref_index}] | {s.score:.2f} | {s.reason} |")
            lines.append("")

        # Uncited references
        cited_indices = set()
        for c in paper.citations:
            cited_indices.update(c.ref_indices)
        uncited = [r for r in paper.references if r.index not in cited_indices]
        if uncited:
            lines.append("## 5. Uncited References\n")
            for r in uncited:
                lines.append(f"- **[{r.index}]** `{r.bib_key}` — {r.title or 'No title'}")
            lines.append("")

        lines.append("---\n*Generated by CiteCheck*")
        return "\n".join(lines)
