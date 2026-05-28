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
            paper.citations = self._extract_citations(body)
            # Resolve author-year citations to reference indices
            self._resolve_author_year_citations(paper)
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
        # Strategy 1: prefer year at the end of the citation (after comma/period)
        year_match = re.search(r"[,\.]\s*(19\d{2}|20\d{2})\s*[\.\n]?$", text)
        if not year_match:
            # Strategy 2: skip arXiv ID patterns like arXiv:2004.05150
            # by removing arXiv IDs before matching
            clean_text = re.sub(r"arXiv[:\s]?\d{4}\.\d{4,5}", "", text, flags=re.I)
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", clean_text)
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
                if ref.year and ref.year in parts[i]:
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

    def _extract_citations(self, body: str) -> List[Citation]:
        """Extract all citation markers from body text.

        Supported formats:
        1. Numbered:        [n]  [n,m]  [n-m]
        2. Superscript:     ¹  ²  ¹²
        3. Parenthetical:   (Author, Year)  (Author Year)  (A & B, Year)
        4. Narrative:       Author (Year)   Author et al. (Year)
        """
        citations = []
        seen = set()

        # 1. Numbered citations [n]  [n,m]  [n-m]  [n–m]
        for match in re.finditer(r"\[([\d\-–,\s]+)\]", body):
            raw = match.group(1)
            nums = self._parse_number_range(raw)
            if not nums:
                continue
            key = ("numbered", tuple(nums))
            if key in seen:
                continue
            seen.add(key)

            start = max(0, match.start() - 150)
            end = min(len(body), match.end() + 150)
            ctx = body[start:end].replace("\n", " ")
            mid = match.start() - start

            citations.append(Citation(
                ref_indices=nums,
                raw_marker=match.group(0),
                context_before=ctx[:mid],
                context_after=ctx[mid + len(match.group(0)):],
            ))

        # 2. Superscript citations (Unicode superscript digits)
        # Match sequences like ¹, ², ¹², ¹²³
        super_pattern = re.compile(
            r"([\u00B9\u00B2\u00B3\u2070-\u2079]+)"
        )
        for match in super_pattern.finditer(body):
            raw = match.group(1)
            nums = self._parse_superscript_digits(raw)
            if not nums:
                continue
            key = ("super", tuple(nums))
            if key in seen:
                continue
            seen.add(key)

            start = max(0, match.start() - 150)
            end = min(len(body), match.end() + 150)
            ctx = body[start:end].replace("\n", " ")
            mid = match.start() - start

            citations.append(Citation(
                ref_indices=nums,
                raw_marker=match.group(0),
                context_before=ctx[:mid],
                context_after=ctx[mid + len(match.group(0)):],
            ))

        # 3. Parenthetical citations (Author, Year)
        # Covers: (Shor, 1994)  (Shor 1994)  (Krithara et al., 2022)
        #         (Krithara & Nentidis, 2022)  (Krithara and Nentidis, 2022)
        paren_pattern = re.compile(
            r"\(\s*"
            r"([A-Z][A-Za-z\.\-]*"
            r"(?:\s+(?:et\s+al\.?|&|and)\s*[A-Za-z\.\-]+)?)"
            r"\s*,?\s*"
            r"(19\d{2}|20\d{2})"
            r"\s*\)"
        )
        for match in paren_pattern.finditer(body):
            author = match.group(1).strip()
            year = match.group(2)
            key = ("paren", author, year)
            if key in seen:
                continue
            seen.add(key)

            start = max(0, match.start() - 150)
            end = min(len(body), match.end() + 150)
            ctx = body[start:end].replace("\n", " ")
            mid = match.start() - start

            citations.append(Citation(
                ref_indices=[],
                raw_marker=match.group(0),
                context_before=ctx[:mid],
                context_after=ctx[mid + len(match.group(0)):],
                bib_keys=[f"{author}|{year}"],
            ))

        # 4. Narrative citations Author (Year)
        # Covers: Shor (1994)  Krithara et al. (2022)
        #         Krithara & Nentidis (2022)
        narrative_pattern = re.compile(
            r"([A-Z][A-Za-z\.\-]*"
            r"(?:\s+(?:et\s+al\.?|&|and)\s*[A-Za-z\.\-]+)?)"
            r"\s+\("
            r"(19\d{2}|20\d{2})"
            r"\)"
        )
        for match in narrative_pattern.finditer(body):
            author = match.group(1).strip()
            year = match.group(2)
            key = ("narrative", author, year)
            if key in seen:
                continue
            seen.add(key)

            start = max(0, match.start() - 150)
            end = min(len(body), match.end() + 150)
            ctx = body[start:end].replace("\n", " ")
            mid = match.start() - start

            citations.append(Citation(
                ref_indices=[],
                raw_marker=match.group(0),
                context_before=ctx[:mid],
                context_after=ctx[mid + len(match.group(0)):],
                bib_keys=[f"{author}|{year}"],
            ))

        return citations

    @staticmethod
    def _parse_number_range(raw: str) -> List[int]:
        """Parse citation range like '1' '1, 2' '1-3' '1–3' into list of ints."""
        nums = []
        # Split by comma first
        parts = [p.strip() for p in raw.split(",")]
        for part in parts:
            # Check for range (dash or en-dash)
            if "-" in part or "–" in part:
                # Normalize en-dash to dash
                part = part.replace("–", "-")
                try:
                    start, end = part.split("-", 1)
                    start, end = int(start.strip()), int(end.strip())
                    nums.extend(range(start, end + 1))
                except ValueError:
                    continue
            else:
                try:
                    nums.append(int(part))
                except ValueError:
                    continue
        return nums

    @staticmethod
    def _parse_superscript_digits(text: str) -> List[int]:
        """Convert Unicode superscript digits to regular ints."""
        mapping = {
            "\u2070": "0", "\u00B9": "1", "\u00B2": "2", "\u00B3": "3",
            "\u2074": "4", "\u2075": "5", "\u2076": "6",
            "\u2077": "7", "\u2078": "8", "\u2079": "9",
        }
        digits = "".join(mapping.get(ch, "") for ch in text)
        if not digits:
            return []
        # Each digit is a separate citation index
        return [int(d) for d in digits]

    def _resolve_author_year_citations(self, paper: Paper) -> None:
        """Map (Author, Year) citations to reference indices."""
        if not paper.references or not paper.citations:
            return

        # Build lookup: (author_last_name, year) -> index
        ref_lookup = {}
        for ref in paper.references:
            if ref.authors and ref.year:
                # Extract last name of first author
                first_author = ref.authors.split(",")[0].strip()
                # Strip common suffixes like "et al.", "and others", "and colleagues"
                first_author = re.sub(
                    r"\s+(?:et\s+al\.?|and\s+others?|and\s+colleagues?)\s*$",
                    "", first_author, flags=re.I,
                )
                last_name = first_author.split()[-1] if first_author else ""
                if last_name:
                    ref_lookup[(last_name.lower(), ref.year)] = ref.index

        for cite in paper.citations:
            if cite.ref_indices:
                continue  # Already resolved (numbered or superscript citation)
            if not cite.bib_keys:
                continue

            for key in cite.bib_keys:
                if "|" not in key:
                    continue
                author_part, year = key.split("|", 1)
                # Strip "et al.", "and others" etc. before matching
                author_part = re.sub(
                    r"\s+(?:et\s+al\.?|and\s+others?|and\s+colleagues?)\s*$",
                    "", author_part, flags=re.I,
                )
                # Try to match by last name
                author_last = author_part.split()[-1].lower() if author_part else ""
                if (author_last, year) in ref_lookup:
                    cite.ref_indices.append(ref_lookup[(author_last, year)])
                    break
                # Fallback: try partial match
                for (ref_last, ref_year), idx in ref_lookup.items():
                    if ref_year == year and (ref_last in author_last or author_last in ref_last):
                        cite.ref_indices.append(idx)
                        break
