from citecheck.matcher import SemanticMatcher, ThematicMatcher, _LLMBase
from citecheck.models import Citation, Paper, Reference
from citecheck.verifier import CitationVerifier, QueryResult


def test_extract_json_score_parses_json_and_float_text():
    assert _LLMBase._extract_json_score('{"score": 0.8, "reason": "ok"}') == (0.8, "ok")

    score, reason = _LLMBase._extract_json_score("score is 0.7 overall")
    assert score == 0.7
    assert "0.7" in reason


def test_thematic_matcher_heuristics_cover_branches():
    matcher = ThematicMatcher()
    paper = Paper(title="BioASQ benchmark study", abstract="biomedical focus")

    score, _ = matcher._heuristic_score(paper, Reference(index=1, title="BioASQ dataset"))
    assert score == 1.0

    score, _ = matcher._heuristic_score(
        paper,
        Reference(index=2, title="Biomedical clinical methods"),
    )
    assert score == 0.8

    score, _ = matcher._heuristic_score(
        paper,
        Reference(index=3, title="Prompt reasoning approach"),
    )
    assert score == 0.7


def test_semantic_matcher_uses_heuristic_and_abstract_map():
    matcher = SemanticMatcher(
        query_results=[
            QueryResult(ref_index=1, matched_abstract="biomedical transformer reasoning")
        ]
    )
    paper = Paper(
        references=[Reference(index=1, title="Transformer Biomedical Model", authors="Doe, Jane")],
        citations=[
            Citation(
                ref_indices=[1],
                context_before="This biomedical transformer",
                context_after="is used",
            )
        ],
    )

    results = matcher.evaluate(paper)

    assert len(results) == 1
    assert results[0].score >= 0.7


def test_verifier_source_fallback_order_and_not_found(monkeypatch):
    verifier = CitationVerifier(skip_online=False)
    verifier.session = object()
    ref = Reference(index=1, title="Some title")

    calls = []

    def miss(name):
        def _fn(_):
            calls.append(name)
            return None

        return _fn

    monkeypatch.setattr(verifier, "_query_crossref", miss("crossref"))
    monkeypatch.setattr(verifier, "_query_semantic_scholar", miss("semantic"))
    monkeypatch.setattr(verifier, "_query_openalex", miss("openalex"))
    monkeypatch.setattr(verifier, "_query_pubmed", miss("pubmed"))
    monkeypatch.setattr(verifier, "_query_arxiv", miss("arxiv"))

    def dblp_hit(_):
        calls.append("dblp")
        return QueryResult(ref_index=1, found=True, source="dblp")

    monkeypatch.setattr(verifier, "_query_dblp", dblp_hit)
    monkeypatch.setattr(verifier, "_query_google_scholar", miss("google"))
    monkeypatch.setattr(verifier, "_query_web_search", miss("web"))

    result = verifier._query_all_sources(ref)

    assert result.found is True
    assert result.source == "dblp"
    assert calls == ["crossref", "semantic", "openalex", "pubmed", "arxiv", "dblp"]


def test_verifier_not_found_and_static_helpers():
    verifier = CitationVerifier(skip_online=True)

    assert verifier.verify_queryability([Reference(index=1)]) == []
    assert CitationVerifier._title_similarity("A Study on Models", "Study of Models") > 0
    assert CitationVerifier._author_overlap(
        "Shor, Peter",
        [{"family": "Shor"}],
    )

    # No session path should also return empty
    verifier = CitationVerifier(skip_online=False)
    verifier.session = None
    assert verifier.verify_queryability([Reference(index=1)]) == []
