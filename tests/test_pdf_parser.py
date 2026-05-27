"""Tests for PDF parser citation extraction."""

import pytest
from citecheck.pdf_parser import PDFParser
from citecheck.models import Citation, Paper, Reference


class TestNumberedCitations:
    """Test [n], [n,m], [n-m] formats."""

    def test_single_number(self):
        parser = PDFParser()
        body = "Recent work [1] has shown great promise."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].ref_indices == [1]
        assert citations[0].raw_marker == "[1]"

    def test_multiple_numbers(self):
        parser = PDFParser()
        body = "See also [1, 2] and [3, 4, 5]."
        citations = parser._extract_citations(body)
        assert len(citations) == 2
        assert sorted(citations[0].ref_indices) == [1, 2]
        assert sorted(citations[1].ref_indices) == [3, 4, 5]

    def test_range_hyphen(self):
        parser = PDFParser()
        body = "Multiple studies [1-3] support this claim."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].ref_indices == [1, 2, 3]
        assert citations[0].raw_marker == "[1-3]"

    def test_range_endash(self):
        parser = PDFParser()
        body = "Multiple studies [1–3] support this claim."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].ref_indices == [1, 2, 3]

    def test_mixed_range_and_single(self):
        parser = PDFParser()
        body = "See [1-3, 5] for details."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].ref_indices == [1, 2, 3, 5]

    def test_deduplication(self):
        parser = PDFParser()
        body = "Work [1] is cited. Work [1] again."
        citations = parser._extract_citations(body)
        # Same index should be deduplicated
        assert len(citations) == 1
        assert citations[0].ref_indices == [1]


class TestSuperscriptCitations:
    """Test Unicode superscript digit citations."""

    def test_single_superscript(self):
        parser = PDFParser()
        body = "Previous work\u00B9 showed this."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].ref_indices == [1]
        assert citations[0].raw_marker == "\u00B9"

    def test_multiple_superscripts(self):
        parser = PDFParser()
        body = "Studies\u00B9\u00B2\u00B3 confirm this."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].ref_indices == [1, 2, 3]

    def test_superscript_zero(self):
        parser = PDFParser()
        body = "Reference\u2070 is the introduction."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].ref_indices == [0]


class TestParentheticalAuthorYear:
    """Test (Author, Year) and variants."""

    def test_simple_comma(self):
        parser = PDFParser()
        body = "This was shown by (Shor, 1994)."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].raw_marker == "(Shor, 1994)"
        assert citations[0].bib_keys == ["Shor|1994"]
        assert citations[0].ref_indices == []

    def test_no_comma(self):
        parser = PDFParser()
        body = "This was shown by (Shor 1994)."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].raw_marker == "(Shor 1994)"
        assert citations[0].bib_keys == ["Shor|1994"]

    def test_et_al(self):
        parser = PDFParser()
        body = "As demonstrated (Krithara et al., 2022)."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert "Krithara" in citations[0].bib_keys[0]
        assert "2022" in citations[0].bib_keys[0]

    def test_ampersand_coauthor(self):
        parser = PDFParser()
        body = "Joint work (Krithara & Nentidis, 2022)."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert "Krithara" in citations[0].bib_keys[0]

    def test_and_coauthor(self):
        parser = PDFParser()
        body = "Joint work (Krithara and Nentidis, 2022)."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert "Krithara" in citations[0].bib_keys[0]

    def test_hyphenated_name(self):
        parser = PDFParser()
        body = "Study by (Smith-Jones, 2018)."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].bib_keys == ["Smith-Jones|2018"]


class TestNarrativeAuthorYear:
    """Test Author (Year) and variants."""

    def test_simple(self):
        parser = PDFParser()
        body = "Shor (1994) proved this theorem."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert citations[0].raw_marker == "Shor (1994)"
        assert citations[0].bib_keys == ["Shor|1994"]

    def test_et_al(self):
        parser = PDFParser()
        body = "Krithara et al. (2022) proposed a new method."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert "Krithara" in citations[0].bib_keys[0]

    def test_ampersand(self):
        parser = PDFParser()
        body = "Krithara & Nentidis (2022) collaborated."
        citations = parser._extract_citations(body)
        assert len(citations) == 1
        assert "Krithara" in citations[0].bib_keys[0]

    def test_no_false_match_on_parenthetical(self):
        """Ensure (Author, Year) is NOT also captured as narrative."""
        parser = PDFParser()
        body = "As shown (Shor, 1994)."
        citations = parser._extract_citations(body)
        # Should only match parenthetical, not narrative
        assert len(citations) == 1
        assert citations[0].raw_marker == "(Shor, 1994)"


class TestAuthorYearResolution:
    """Test mapping author-year citations to reference indices."""

    def test_resolve_single_author(self):
        parser = PDFParser()
        paper = Paper(source_type="pdf")
        paper.references = [
            Reference(index=1, authors="Peter W. Shor", year="1994", title="Algorithms"),
            Reference(index=2, authors="Anastasia Krithara", year="2022", title="BioASQ"),
        ]
        paper.citations = [
            Citation(ref_indices=[], bib_keys=["Shor|1994"]),
            Citation(ref_indices=[], bib_keys=["Krithara|2022"]),
        ]
        parser._resolve_author_year_citations(paper)
        assert paper.citations[0].ref_indices == [1]
        assert paper.citations[1].ref_indices == [2]

    def test_resolve_et_al(self):
        parser = PDFParser()
        paper = Paper(source_type="pdf")
        paper.references = [
            Reference(index=1, authors="Anastasia Krithara and others", year="2022", title="BioASQ"),
        ]
        paper.citations = [
            Citation(ref_indices=[], bib_keys=["Krithara et al.|2022"]),
        ]
        parser._resolve_author_year_citations(paper)
        assert paper.citations[0].ref_indices == [1]

    def test_no_match_leaves_empty(self):
        parser = PDFParser()
        paper = Paper(source_type="pdf")
        paper.references = [
            Reference(index=1, authors="Albert Einstein", year="1905", title="Photoelectric"),
        ]
        paper.citations = [
            Citation(ref_indices=[], bib_keys=["Newton|1687"]),
        ]
        parser._resolve_author_year_citations(paper)
        assert paper.citations[0].ref_indices == []

    def test_already_resolved_skipped(self):
        parser = PDFParser()
        paper = Paper(source_type="pdf")
        paper.references = [
            Reference(index=1, authors="Peter W. Shor", year="1994", title="Algorithms"),
        ]
        paper.citations = [
            Citation(ref_indices=[1], bib_keys=[]),
        ]
        parser._resolve_author_year_citations(paper)
        assert paper.citations[0].ref_indices == [1]  # Unchanged
