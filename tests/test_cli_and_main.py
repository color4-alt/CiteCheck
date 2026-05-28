import runpy
import sys
from pathlib import Path

import pytest

from citecheck import cli
from citecheck.matcher import MatchResult
from citecheck.models import Citation, Paper, Reference


class _FakeVerifier:
    def __init__(self, skip_online=False):
        self.skip_online = skip_online

    def check_format(self, refs):
        return refs

    def verify_queryability(self, refs):
        return []


class _FakeThematicMatcher:
    def __init__(self, api_key=None):
        self.api_key = api_key

    def evaluate(self, paper):
        return [MatchResult(ref_index=1, score=0.5, reason="ok")]


class _FakeSemanticMatcher:
    def __init__(self, api_key=None, query_results=None):
        self.api_key = api_key
        self.query_results = query_results or []

    def evaluate(self, paper):
        return [MatchResult(ref_index=1, score=0.6, reason="ok")]


class _FakeReportGenerator:
    def generate(self, **kwargs):
        return "report body"


def test_cli_main_happy_path_writes_report(monkeypatch, tmp_path: Path):
    input_file = tmp_path / "paper.tex"
    output_file = tmp_path / "report.md"
    input_file.write_text("dummy", encoding="utf-8")

    fake_paper = Paper(
        source_type="latex",
        references=[Reference(index=1, title="Ref")],
        citations=[Citation(ref_indices=[1], raw_marker="[1]")],
    )

    class _FakePaperParser:
        def parse(self, path):
            assert path == input_file
            return fake_paper

    monkeypatch.setattr(cli, "PaperParser", _FakePaperParser)
    monkeypatch.setattr(cli, "CitationVerifier", _FakeVerifier)
    monkeypatch.setattr(cli, "ThematicMatcher", _FakeThematicMatcher)
    monkeypatch.setattr(cli, "SemanticMatcher", _FakeSemanticMatcher)
    monkeypatch.setattr(cli, "ReportGenerator", _FakeReportGenerator)
    monkeypatch.setattr(
        sys,
        "argv",
        ["citecheck", str(input_file), "-o", str(output_file)],
    )

    cli.main()

    assert output_file.read_text(encoding="utf-8") == "report body"


def test_cli_main_missing_input_exits(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["citecheck", "/tmp/does-not-exist.tex"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1


def test_module_main_invokes_cli_main(monkeypatch):
    called = {"value": False}

    def fake_main():
        called["value"] = True

    monkeypatch.setattr("citecheck.cli.main", fake_main)
    runpy.run_module("citecheck.__main__", run_name="__main__")

    assert called["value"] is True
