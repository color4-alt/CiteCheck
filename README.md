# Paper Citation Check

A command-line tool for verifying academic paper citations. Supports **LaTeX source files** (preferred) and **PDF** (fallback).

## Features

- **Format Check**: Validates BibTeX entries and PDF-extracted references for required fields, type consistency, and common errors
- **Queryability Verification**: Checks if cited papers exist via Crossref and Semantic Scholar APIs
- **Thematic Relevance**: Scores how relevant each citation is to the paper's topic
- **Semantic Accuracy**: Evaluates whether in-text claims match the cited source's content
- **LaTeX-first Parsing**: Prioritizes `.tex` + `.bib` sources for precise citation tracking; falls back to PDF text extraction

## Installation

```bash
pip install CiteCheck
```

For PDF support, also install:

```bash
pip install CiteCheck[pdf]
```

Or from source:

```bash
git clone https://github.com/yourusername/CiteCheck.git
cd CiteCheck
pip install -e ".[pdf,dev]"
```

## Quick Start

### Check a LaTeX project

```bash
citecheck path/to/latex_project/
```

The tool looks for `.tex` and `.bib` files in the directory.

### Check a single PDF

```bash
citecheck paper.pdf -o report.md
```

### Check a single .tex file

```bash
citecheck main.tex
```

## Usage

```
citecheck [-h] [-o OUTPUT] [--skip-verification] [--skip-semantic] [--api-key API_KEY] [-v] input

positional arguments:
  input                 Path to the paper file (PDF, .tex, or directory with .tex + .bib)

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output report path (default: citation_check_report.md)
  --skip-verification   Skip online verification (Crossref/Semantic Scholar)
  --skip-semantic       Skip semantic matching
  --api-key API_KEY     OpenAI API key for semantic matching
  -v, --verbose         Verbose output
```

## Workflow

```
Input (PDF / LaTeX / .bib)
    │
    ▼
┌─────────────────┐
│ 1. Parse Paper  │  ← Extract refs, citations, body text
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌─────────────┐
│LaTeX   │ │ PDF Fallback │
│(.bib)  │ │ (PyMuPDF)    │
└────────┘ └─────────────┘
         │
         ▼
┌─────────────────┐
│ 2. Format Check │  ← Validate BibTeX fields, types, DOIs
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ 3. Queryability     │  ← Crossref → Semantic Scholar
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 4. Thematic Match   │  ← Paper topic vs. cited paper topic
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 5. Semantic Match   │  ← In-text claim vs. source content
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ 6. Generate Report  │  ← Markdown report with findings
└─────────────────────┘
```

## Report Example

The tool generates a Markdown report including:

- **Summary table**: total refs, format issues, verified count, average scores
- **Detailed results table**: per-reference format/queryable/thematic/semantic status
- **Format issues**: specific problems (missing DOI, wrong entry type, year mismatch, etc.)
- **Queryability results**: verification status from Crossref/Semantic Scholar
- **Uncited references**: entries in `.bib` that are never `\cite{}`'d in the text

See [`examples/example_report.md`](examples/example_report.md) for a sample output.

## Project Structure

```
CiteCheck/
├── src/citecheck/
│   ├── __init__.py
│   ├── cli.py              # Command-line entry point
│   ├── parser.py           # Paper parser (LaTeX / PDF dispatcher)
│   ├── bibtex_parser.py    # BibTeX .bib file parser
│   ├── pdf_parser.py       # PDF text extraction and citation parsing
│   ├── verifier.py         # Crossref / Semantic Scholar API verification
│   ├── matcher.py          # Thematic and semantic scoring
│   └── reporter.py         # Markdown report generator
├── scripts/
│   └── check_citations.py  # Standalone script
├── references/
│   ├── semantic-matching-prompt.md
│   ├── api-reference.md
│   └── format-check-rules.md
├── tests/
│   └── test_parser.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## Supported Input Formats

| Format | Priority | Notes |
|--------|----------|-------|
| LaTeX directory | 1st | Requires `.tex` + `.bib`; resolves `\input{}` |
| Single `.tex` file | 2nd | Looks for sibling `.bib` file |
| PDF | Fallback | Extracts text via PyMuPDF; less precise than LaTeX |

## API Keys

- **Online verification** uses Crossref and Semantic Scholar public APIs (no key needed, but rate-limited)
- **Semantic matching** uses built-in heuristics by default; for LLM-powered matching, set `OPENAI_API_KEY` or pass `--api-key`

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/
```

## License

MIT License — see [LICENSE](LICENSE).
