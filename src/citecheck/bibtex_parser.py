"""BibTeX bibliography parser."""

import re
from typing import List

from citecheck.models import Reference


class BibTeXParser:
    """Parse BibTeX .bib files into structured references."""

    def parse(self, bib_content: str) -> List[Reference]:
        """Parse raw BibTeX content into Reference objects."""
        entries = self._split_entries(bib_content)
        refs = []
        for idx, raw_entry in enumerate(entries, 1):
            ref = self._parse_entry(idx, raw_entry)
            if ref:
                refs.append(ref)
        return refs

    def _split_entries(self, content: str) -> List[str]:
        """Split BibTeX content into individual entries."""
        entries = []
        depth = 0
        current = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("@"):
                if current:
                    entries.append("\n".join(current))
                current = [line]
                depth = 1 if "{" in stripped else 0
            elif current:
                current.append(line)
                depth += line.count("{") - line.count("}")
                if depth == 0 and stripped == "}":
                    entries.append("\n".join(current))
                    current = []
        if current:
            entries.append("\n".join(current))
        return entries

    def _parse_entry(self, index: int, raw: str) -> Reference:
        """Parse a single BibTeX entry."""
        header_match = re.match(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", raw.strip())
        if not header_match:
            return None

        entry_type = header_match.group(1).lower()
        bib_key = header_match.group(2)
        body = raw[header_match.end():]

        fields = self._extract_fields(body)

        ref = Reference(
            index=index,
            bib_key=bib_key,
            entry_type=entry_type,
            raw_text=raw.strip(),
            title=fields.get("title", ""),
            authors=fields.get("author", ""),
            year=fields.get("year"),
            venue=fields.get("journal") or fields.get("booktitle") or "",
            doi=fields.get("doi"),
            volume=fields.get("volume"),
            number=fields.get("number"),
            pages=fields.get("pages"),
            url=fields.get("url"),
        )
        ref.issues = self._check_format_issues(ref)
        return ref

    def _extract_fields(self, body: str) -> dict:
        """Extract key-value pairs from BibTeX entry body."""
        fields = {}
        pattern = re.compile(
            r"(\w+)\s*=\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\"[^\"]*\")",
            re.DOTALL
        )
        for match in pattern.finditer(body):
            key = match.group(1).lower()
            value = match.group(2)
            # Remove outer braces/quotes
            if value.startswith("{") and value.endswith("}"):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            # Clean up whitespace
            value = " ".join(value.split())
            fields[key] = value
        return fields

    def _check_format_issues(self, ref: Reference) -> List[str]:
        """Check for common BibTeX format issues."""
        issues = []

        if not ref.title:
            issues.append("Missing title")
        if not ref.authors:
            issues.append("Missing author")
        if not ref.year:
            issues.append("Missing year")

        # Entry type checks
        if ref.entry_type == "article" and not (ref.venue or ref.volume):
            issues.append("Article missing journal/volume")
        if ref.entry_type == "inproceedings" and not ref.venue:
            issues.append("Inproceedings missing booktitle")

        # Preprint vs published
        venue_lower = (ref.venue or "").lower()
        if "arxiv" in venue_lower or "biorxiv" in venue_lower or "medrxiv" in venue_lower:
            issues.append(f"Preprint source: {ref.venue}")

        # Year sanity
        if ref.year:
            try:
                y = int(ref.year)
                if y > 2026 or y < 1900:
                    issues.append(f"Suspicious year: {ref.year}")
            except ValueError:
                issues.append(f"Invalid year: {ref.year}")

        # Booktitle vs journal for known journals
        if ref.entry_type == "inproceedings":
            known_journals = ["bmc bioinformatics", "bioinformatics", "nature", "scientific data"]
            if any(j in venue_lower for j in known_journals):
                issues.append(f"Should be @article, not @inproceedings (venue is a journal)")

        return issues
