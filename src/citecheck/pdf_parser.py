"""PDF paper parser using PyMuPDF (fitz) as fallback."""

import re
from pathlib import Path
from typing import List

from citecheck.models import Citation, Paper, Reference


class PDFParser:
    """Parse academic papers from PDF files."""

    def parse(self, path: Path) -> Paper:
        try:
            import fitz
        except ImportError:
            raise ImportError(
                "PyMuPDF (fitz) is required for PDF parsing. "
                "Install with: pip install PyMuPDF"
            )

        doc = fitz.open(str(path))
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        paper = Paper(source_type="pdf")
        paper.body_text = full_text

        # Extract references section
        ref_start = self._find_reference_section(full_text)
        if ref_start >= 0:
            body = full_text[:ref_start]
            ref_section = full_text[ref_start:]
            paper.references = self._extract_numbered_references(ref_section)
            paper.citations = self._extract_numbered_citations(body)
        else:
            paper.references = []
            paper.citations = []

        return paper

    def _find_reference_section(self, text: str) -> int:
        """Find the start of the references section."""
        markers = [
            "\nReferences\n", "\nREFERENCES\n",
            "\nBibliography\n", "\nBIBLIOGRAPHY\n",
            "参考文献", "\nReference\n",
        ]
        for marker in markers:
            idx = text.find(marker)
            if idx >= 0:
                return idx
        # Fallback: look for numbered reference patterns near end
        lines = text.splitlines()
        for i in range(len(lines) - 1, max(0, len(lines) - 50), -1):
            if re.match(r"^\[?1\]?[.\s]", lines[i]):
                return text.find(lines[i])
        return -1

    def _extract_numbered_references(self, ref_section: str) -> List[Reference]:
        """Extract numbered references from text."""
        refs = []

        # Strategy 1: BibTeX \bibitem{key} format (common in compiled PDFs)
        bibitem_pattern = re.compile(
            r"\\bibitem\{([^}]*)\}(.*?)(?=\\bibitem|$)",
            re.DOTALL
        )
        bibitem_matches = list(bibitem_pattern.finditer(ref_section))
        if bibitem_matches:
            for idx, match in enumerate(bibitem_matches, 1):
                key = match.group(1)
                raw = " ".join(match.group(2).split())
                ref = self._parse_reference_text(idx, raw)
                ref.bib_key = key
                refs.append(ref)
            return refs

        # Strategy 2: Numbered [1] or 1. format
        pattern = re.compile(
            r"(?:^|\n)\[(\d+)\]\s+"
            r"(.*?)"
            r"(?=(?:\n\[\d+\]\s)|$)",
            re.DOTALL
        )
        for match in pattern.finditer(ref_section):
            idx = int(match.group(1))
            raw = " ".join(match.group(2).split())
            refs.append(self._parse_reference_text(idx, raw))
        if refs:
            return refs

        # Strategy 3: Fallback to simple numbered list
        pattern = re.compile(
            r"(?:^|\n)(\d+)[.\s]+"
            r"(.*?)"
            r"(?=(?:\n\d+[.\s])|$)",
            re.DOTALL
        )
        for match in pattern.finditer(ref_section):
            idx = int(match.group(1))
            raw = " ".join(match.group(2).split())
            refs.append(self._parse_reference_text(idx, raw))
        return refs

    def _parse_reference_text(self, index: int, text: str) -> Reference:
        """Parse a single reference text into structured fields."""
        ref = Reference(index=index, raw_text=text)

        # Try to extract year (4-digit number 19xx or 20xx)
        year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
        if year_match:
            ref.year = year_match.group(1)

        # Try to split authors and title
        # Common patterns:
        #   Author. Title. Venue, Year.
        #   Author. \newblock Title. \newblock Venue, Year.
        text = text.replace("\\newblock", " ")
        parts = re.split(r"\.\s+", text)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) >= 2:
            ref.authors = parts[0]
            # Title is usually before venue/year pattern
            for i in range(1, len(parts)):
                if year_match and year_match.group(1) in parts[i]:
                    ref.title = ". ".join(parts[1:i]).strip(". ")
                    ref.venue = ". ".join(parts[i:]).strip(". ")
                    break
            if not ref.title:
                ref.title = parts[1]
                if len(parts) > 2:
                    ref.venue = ". ".join(parts[2:]).strip(". ")

        ref.issues = self._check_pdf_ref_issues(ref)
        return ref

    def _check_pdf_ref_issues(self, ref: Reference) -> List[str]:
        """Check format issues for PDF-extracted references."""
        issues = []
        if not ref.authors:
            issues.append("Missing author")
        if not ref.title:
            issues.append("Missing title")
        if not ref.year:
            issues.append("Missing year")
        if not ref.venue:
            issues.append("Missing venue")
        return issues

    def _extract_numbered_citations(self, body: str) -> List[Citation]:
        """Extract [n] citation markers from body text."""
        citations = []
        seen = set()
        for match in re.finditer(r"\[(\d+(?:,\s*\d+)*)\]", body):
            raw = match.group(1)
            nums = tuple(int(n) for n in re.findall(r"\d+", raw))
            if nums in seen:
                continue
            seen.add(nums)

            start = max(0, match.start() - 150)
            end = min(len(body), match.end() + 150)
            ctx = body[start:end].replace("\n", " ")
            mid = match.start() - start

            citations.append(Citation(
                ref_indices=list(nums),
                raw_marker=match.group(0),
                context_before=ctx[:mid],
                context_after=ctx[mid + len(match.group(0)):],
            ))
        return citations
