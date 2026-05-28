from citecheck.matcher import MatchResult
from citecheck.models import Citation, Paper, Reference
from citecheck.reporter import ReportGenerator
from citecheck.verifier import QueryResult


def test_report_generator_includes_sections_and_uncited_reference():
    paper = Paper(
        title="Demo Paper",
        source_type="latex",
        references=[
            Reference(index=1, bib_key="a", title="Ref A", issues=["Missing year"]),
            Reference(index=2, bib_key="b", title="Ref B"),
        ],
        citations=[Citation(ref_indices=[1], raw_marker="[1]")],
    )

    report = ReportGenerator().generate(
        paper=paper,
        format_results=paper.references,
        query_results=[
            QueryResult(
                ref_index=1,
                found=True,
                source="Crossref",
                matched_title="Matched title",
                matched_year="2020",
                warnings=["Check venue"],
            )
        ],
        thematic_results=[MatchResult(ref_index=1, score=0.9, reason="Relevant")],
        semantic_results=[MatchResult(ref_index=1, score=0.8, reason="Consistent")],
    )

    assert "# Citation Check Report" in report
    assert "## 1. Format Check Details" in report
    assert "## 2. Queryability Verification" in report
    assert "## 3. Thematic Relevance" in report
    assert "## 4. Semantic Accuracy" in report
    assert "## 5. Uncited References" in report
    assert "Check venue" in report
    assert "**[2]** `b`" in report


def test_report_generator_handles_empty_optional_results():
    paper = Paper(source_type="pdf", references=[Reference(index=1, bib_key="x")], citations=[])

    report = ReportGenerator().generate(
        paper=paper,
        format_results=paper.references,
        query_results=[],
        thematic_results=[],
        semantic_results=[],
    )

    assert "All references pass basic format checks" in report
    assert "## 2. Queryability Verification" not in report
    assert "## 3. Thematic Relevance" not in report
    assert "## 4. Semantic Accuracy" not in report
