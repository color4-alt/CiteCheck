"""Paper parser supporting LaTeX (preferred) and PDF (fallback)."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .bibtex_parser import BibTeXParser
from .pdf_parser import PDFParser


@dataclass
class Reference:
    """A single bibliographic reference."""
    index: int
    bib_key: Optional[str] = None
    raw_text: str = ""
    entry_type: Optional[str] = None
    title: str = ""
    authors: str = ""
    year: Optional[str] = None
    venue: str = ""
    doi: Optional[str] = None
    volume: Optional[str] = None
    number: Optional[str] = None
    pages: Optional[str] = None
    url: Optional[str] = None
    issues: List[str] = field(default_factory=list)


@dataclass
class Citation:
    """An in-text citation with its context."""
    ref_indices: List[int]
    context_before: str = ""
    context_after: str = ""
    raw_marker: str = ""


@dataclass
class Paper:
    """Parsed paper content."""
    title: str = ""
    abstract: str = ""
    keywords: str = ""
    references: List[Reference] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    body_text: str = ""
    source_type: str = ""  # "latex" or "pdf"


class PaperParser:
    """Parse academic papers from LaTeX source (preferred) or PDF."""

    def parse(self, path: Path) -> Paper:
        if path.is_dir():
            return self._parse_latex_dir(path)
        if path.suffix.lower() == ".tex":
            return self._parse_latex_file(path)
        if path.suffix.lower() == ".pdf":
            return self._parse_pdf(path)
        raise ValueError(f"Unsupported file type: {path.suffix}")

    def _parse_latex_dir(self, directory: Path) -> Paper:
        """Parse a LaTeX project directory."""
        tex_files = list(directory.glob("*.tex"))
        bib_files = list(directory.glob("*.bib"))

        if not tex_files:
            raise FileNotFoundError(f"No .tex file found in {directory}")

        main_tex = tex_files[0]
        for tf in tex_files:
            content = tf.read_text(encoding="utf-8", errors="ignore")
            if "\\begin{document}" in content:
                main_tex = tf
                break

        tex_content = main_tex.read_text(encoding="utf-8", errors="ignore")
        paper = Paper(source_type="latex")

        # Extract title
        title_match = re.search(r"\\title\{([^}]*)\}", tex_content)
        if title_match:
            paper.title = self._clean_latex(title_match.group(1))

        # Extract abstract
        abs_match = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex_content, re.DOTALL)
        if abs_match:
            paper.abstract = self._clean_latex(abs_match.group(1))

        # Read all included sections
        body = self._resolve_inputs(directory, tex_content)
        paper.body_text = body

        # Extract citations
        paper.citations = self._extract_latex_citations(body)

        # Parse bibliography
        if bib_files:
            bib_path = bib_files[0]
            bib_content = bib_path.read_text(encoding="utf-8", errors="ignore")
            paper.references = BibTeXParser().parse(bib_content)
        else:
            # Try to extract thebibliography from .tex
            paper.references = self._extract_thebibliography(body)

        return paper

    def _parse_latex_file(self, path: Path) -> Paper:
        return self._parse_latex_dir(path.parent)

    def _parse_pdf(self, path: Path) -> Paper:
        """Parse PDF as fallback."""
        return PDFParser().parse(path)

    def _resolve_inputs(self, directory: Path, tex_content: str) -> str:
        """Resolve \\input{} directives."""
        pattern = r"\\input\{([^}]+)\}"
        result = tex_content
        for match in re.finditer(pattern, tex_content):
            input_path = directory / match.group(1)
            if not input_path.suffix:
                input_path = input_path.with_suffix(".tex")
            if input_path.exists():
                sub_content = input_path.read_text(encoding="utf-8", errors="ignore")
                result = result.replace(match.group(0), sub_content)
        return result

    def _extract_latex_citations(self, body: str) -> List[Citation]:
        """Extract \\cite{} markers and their contexts."""
        citations = []
        # Handle \cite{key1,key2} and \citep{}, \citet{}
        for match in re.finditer(r"\\(?:cite|citep|citet)\{([^}]+)\}", body):
            keys = [k.strip() for k in match.group(1).split(",")]
            start = max(0, match.start() - 150)
            end = min(len(body), match.end() + 150)
            context = body[start:end]
            mid = match.start() - start
            citations.append(Citation(
                ref_indices=[],
                raw_marker=match.group(0),
                context_before=context[:mid].replace("\n", " "),
                context_after=context[mid + len(match.group(0)):].replace("\n", " "),
            ))
        return citations

    def _extract_thebibliography(self, body: str) -> List[Reference]:
        """Extract \begin{thebibliography} entries."""
        refs = []
        bib_match = re.search(r"\\begin\{thebibliography\}(.*?)\\end\{thebibliography\}", body, re.DOTALL)
        if not bib_match:
            return refs
        bib_content = bib_match.group(1)
        entries = re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]*)\}(.*?)(?=\\bibitem|$)", bib_content, re.DOTALL)
        for idx, (key, text) in enumerate(entries, 1):
            text = text.replace("\n", " ").strip()
            refs.append(Reference(index=idx, bib_key=key, raw_text=text))
        return refs

    @staticmethod
    def _clean_latex(text: str) -> str:
        """Remove simple LaTeX commands."""
        text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^}]*\})?", "", text)
        text = text.replace("\\", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()
