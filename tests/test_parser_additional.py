from pathlib import Path

import pytest

from citecheck.parser import PaperParser


def test_parse_latex_dir_resolves_inputs_and_bib_keys(tmp_path: Path):
    project = tmp_path / "paper"
    project.mkdir()

    (project / "main.tex").write_text(
        """\\title{A \\textbf{Great} Paper}
\\begin{abstract}We use \\emph{strong} methods.\\end{abstract}
\\begin{document}
Intro text. \\input{section}
\\end{document}
""",
        encoding="utf-8",
    )
    (project / "section.tex").write_text(
        "Prior work \\cite{smith2020}.",
        encoding="utf-8",
    )
    (project / "refs.bib").write_text(
        """@article{smith2020,
  title={Title},
  author={Smith, Jane},
  journal={Journal},
  year={2020}
}
""",
        encoding="utf-8",
    )

    paper = PaperParser().parse(project)

    assert paper.source_type == "latex"
    assert paper.title == "A Paper"
    assert "Prior work" in paper.body_text
    assert "\\input{section}" not in paper.body_text
    assert len(paper.references) == 1
    assert paper.citations[0].bib_keys == ["smith2020"]
    assert paper.citations[0].ref_indices == [1]


def test_parse_latex_dir_uses_thebibliography_when_no_bib(tmp_path: Path):
    project = tmp_path / "paper"
    project.mkdir()

    (project / "main.tex").write_text(
        r"""
\\begin{document}
Text \\cite{key1} and \\cite{key2}.
\\begin{thebibliography}{9}
\\bibitem{key1} Author One. Title One. 2020.
\\bibitem{key2} Author Two. Title Two. 2021.
\\end{thebibliography}
\\end{document}
""",
        encoding="utf-8",
    )

    paper = PaperParser().parse(project)

    assert [r.bib_key for r in paper.references] == ["key1", "key2"]
    assert [c.ref_indices for c in paper.citations] == [[1], [2]]


def test_parse_latex_dir_without_tex_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        PaperParser().parse(tmp_path)


def test_parse_unsupported_suffix_raises(tmp_path: Path):
    file_path = tmp_path / "file.md"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        PaperParser().parse(file_path)


def test_parse_pdf_dispatch_calls_pdf_parser(monkeypatch, tmp_path: Path):
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_text("placeholder", encoding="utf-8")

    called = {"value": False}

    def fake_parse_pdf(self, path: Path):
        called["value"] = True
        assert path == pdf_path
        return "ok"

    monkeypatch.setattr(PaperParser, "_parse_pdf", fake_parse_pdf)

    result = PaperParser().parse(pdf_path)
    assert called["value"] is True
    assert result == "ok"
