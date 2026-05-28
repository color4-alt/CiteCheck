import sys
import types
from pathlib import Path

from citecheck.pdf_parser import PDFParser


class _FakePage:
    def __init__(self, text: str):
        self._text = text

    def get_text(self) -> str:
        return self._text


class _FakeDoc(list):
    def close(self):
        self.closed = True


def test_parse_pdf_end_to_end_with_fake_fitz(monkeypatch, tmp_path: Path):
    parser = PDFParser()
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_text("dummy", encoding="utf-8")

    text = (
        "Intro with citation [1].\n"
        "More content.\n"
        "References\n"
        "[1] Jane Smith. Good Title. Good Venue, 2020.\n"
    )
    fake_doc = _FakeDoc([_FakePage(text)])
    fake_fitz = types.SimpleNamespace(open=lambda _: fake_doc)
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

    paper = parser.parse(pdf_path)

    assert paper.source_type == "pdf"
    assert len(paper.references) == 1
    assert paper.references[0].year == "2020"
    assert paper.citations[0].ref_indices == [1]


def test_parse_pdf_without_reference_section_returns_empty(monkeypatch, tmp_path: Path):
    parser = PDFParser()
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_text("dummy", encoding="utf-8")

    fake_doc = _FakeDoc([_FakePage("No references marker here")])
    fake_fitz = types.SimpleNamespace(open=lambda _: fake_doc)
    monkeypatch.setitem(sys.modules, "fitz", fake_fitz)

    paper = parser.parse(pdf_path)

    assert paper.references == []
    assert paper.citations == []
