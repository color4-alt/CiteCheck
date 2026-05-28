"""Paper parser supporting LaTeX (preferred) and PDF (fallback)."""

import re
from pathlib import Path
from typing import List, Optional, Set

from citecheck.models import Citation, Paper, Reference


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

        if not tex_files:
            raise FileNotFoundError(f"No .tex file found in {directory}")

        main_tex = tex_files[0]
        for tf in tex_files:
            try:
                content = tf.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "\\begin{document}" in content:
                main_tex = tf
                break

        return self._parse_latex_project(directory, main_tex)

    def _parse_latex_file(self, path: Path) -> Paper:
        return self._parse_latex_project(path.parent, path)

    def _parse_latex_project(self, directory: Path, main_tex: Path) -> Paper:
        from .bibtex_parser import BibTeXParser

        bib_files = list(directory.glob("*.bib"))
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

        # Resolve citation ref_indices from bib_keys
        ref_key_to_index = {r.bib_key: r.index for r in paper.references if r.bib_key}
        for cite in paper.citations:
            indices = []
            for key in cite.bib_keys:
                if key in ref_key_to_index:
                    indices.append(ref_key_to_index[key])
            cite.ref_indices = indices

        return paper

    def _parse_pdf(self, path: Path) -> Paper:
        """Parse PDF as fallback."""
        from .pdf_parser import PDFParser
        return PDFParser().parse(path)

    def _resolve_inputs(self, directory: Path, tex_content: str, stack: Optional[Set[Path]] = None) -> str:
        """Resolve \\input{} directives."""
        if stack is None:
            stack = set()

        pattern = re.compile(r"\\input\{([^}]+)\}")

        def _replace(match: re.Match) -> str:
            input_path = directory / match.group(1)
            if not input_path.suffix:
                input_path = input_path.with_suffix(".tex")
            input_path = input_path.resolve()

            if input_path in stack:
                return ""
            if not input_path.exists():
                return match.group(0)

            try:
                sub_content = input_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return match.group(0)

            next_stack = set(stack)
            next_stack.add(input_path)
            return self._resolve_inputs(input_path.parent, sub_content, next_stack)

        return pattern.sub(_replace, tex_content)

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
                bib_keys=keys,
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
