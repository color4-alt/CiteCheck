"""Tests for citation checker parsers."""

import pytest
from citecheck.bibtex_parser import BibTeXParser
from citecheck.parser import PaperParser


SAMPLE_BIB = """\
@article{test2023example,
  title={An Example Paper for Testing},
  author={Doe, John and Smith, Jane},
  journal={Journal of Examples},
  volume={10},
  number={2},
  pages={100--120},
  year={2023},
  doi={10.1000/example.123}
}

@inproceedings{test2022conf,
  title={A Conference Paper},
  author={Alice, Bob},
  booktitle={Proc. of Example Conference},
  pages={50--60},
  year={2022}
}
"""


def test_bibtex_parser_extracts_fields():
    parser = BibTeXParser()
    refs = parser.parse(SAMPLE_BIB)
    assert len(refs) == 2

    ref1 = refs[0]
    assert ref1.bib_key == "test2023example"
    assert ref1.title == "An Example Paper for Testing"
    assert ref1.authors == "Doe, John and Smith, Jane"
    assert ref1.year == "2023"
    assert ref1.venue == "Journal of Examples"
    assert ref1.doi == "10.1000/example.123"
    assert ref1.volume == "10"
    assert ref1.number == "2"
    assert ref1.pages == "100--120"


def test_bibtex_parser_flags_preprint():
    parser = BibTeXParser()
    bib = """\
@article{preprint2024,
  title={My Preprint},
  author={Author, One},
  journal={arXiv preprint arXiv:2401.00001},
  year={2024}
}
"""
    refs = parser.parse(bib)
    assert len(refs) == 1
    assert any("Preprint" in issue for issue in refs[0].issues)


def test_bibtex_parser_no_longer_flags_missing_doi():
    """DOI check removed to reduce noise; verification handles existence."""
    parser = BibTeXParser()
    bib = """\
@article{nodoi2023,
  title={No DOI Paper},
  author={Author, One},
  journal={Some Journal},
  year={2023}
}
"""
    refs = parser.parse(bib)
    assert not any("Missing DOI" in issue for issue in refs[0].issues)


def test_bibtex_parser_flags_wrong_entry_type():
    parser = BibTeXParser()
    bib = """\
@inproceedings{shouldbearticle2023,
  title={Published in a Journal},
  author={Author, One},
  booktitle={BMC bioinformatics},
  year={2023}
}
"""
    refs = parser.parse(bib)
    assert refs[0].entry_type == "inproceedings"
    assert any("@article" in issue for issue in refs[0].issues)


def test_bibtex_parser_flags_incomplete_entry():
    parser = BibTeXParser()
    bib = """\
@article{incomplete2023,
  title={Study on Something Important},
  year={2023}
}
"""
    refs = parser.parse(bib)
    assert len(refs) == 1
    assert any("Missing author" in issue for issue in refs[0].issues)
    assert any("missing journal" in issue.lower() for issue in refs[0].issues)


def test_bibtex_parser_flags_future_year():
    parser = BibTeXParser()
    bib = """\
@article{future2030,
  title={Advanced Neural Methods},
  author={Smith, John},
  journal={Nature Biotechnology},
  year={2030}
}
"""
    refs = parser.parse(bib)
    assert len(refs) == 1
    assert any("Suspicious year" in issue for issue in refs[0].issues)


def test_paper_parser_detects_tex_vs_pdf():
    from pathlib import Path
    parser = PaperParser()
    # Just verify the dispatch logic doesn't crash on unknown types
    with pytest.raises(ValueError):
        parser.parse(Path(__file__))  # .py file should raise


def test_latex_citation_key_resolution():
    r"""Ensure \cite{key} maps to correct reference indices."""
    from citecheck.models import Citation, Reference
    from citecheck.parser import PaperParser

    parser = PaperParser()
    # Simulate a simple tex body with citations
    body = (
        "Recent advances in biomedical QA \\cite{lee2020biobert,gu2021domain} "
        "have shown great promise \\cite{wei2022chainofthought}."
    )
    citations = parser._extract_latex_citations(body)
    assert len(citations) == 2

    # First citation has two keys
    assert citations[0].bib_keys == ["lee2020biobert", "gu2021domain"]
    # Second citation has one key
    assert citations[1].bib_keys == ["wei2022chainofthought"]

    # Simulate resolving keys to indices
    refs = [
        Reference(index=1, bib_key="lee2020biobert", title="BioBERT"),
        Reference(index=2, bib_key="gu2021domain", title="PubMedBERT"),
        Reference(index=3, bib_key="wei2022chainofthought", title="CoT"),
    ]
    ref_key_to_index = {r.bib_key: r.index for r in refs if r.bib_key}
    for cite in citations:
        indices = []
        for key in cite.bib_keys:
            if key in ref_key_to_index:
                indices.append(ref_key_to_index[key])
        cite.ref_indices = indices

    assert citations[0].ref_indices == [1, 2]
    assert citations[1].ref_indices == [3]
