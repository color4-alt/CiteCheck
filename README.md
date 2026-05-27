<p align="center">
  <img src="assets/banner.jpg" alt="CiteCheck Banner" width="100%">
</p>

# Paper Citation Check

A command-line tool and **cross-agent skill** for verifying academic paper citations. Supports **LaTeX source files** (preferred) and **PDF** (fallback).

Works with Claude Code, Codex CLI, OpenClaw, Hermes, Gemini CLI, Cursor, and more.

## Features

- **Format Check**: Validates BibTeX entries and PDF-extracted references for required fields, type consistency, and common errors
- **Queryability Verification**: Checks if cited papers exist via Crossref and Semantic Scholar APIs
- **Thematic Relevance**: Scores how relevant each citation is to the paper's topic
- **Semantic Accuracy**: Evaluates whether in-text claims match the cited source's content
- **LaTeX-first Parsing**: Prioritizes `.tex` + `.bib` sources for precise citation tracking; falls back to PDF text extraction
- **Cross-Agent Skill**: Use as a standalone CLI or as an agent skill (Claude, Codex, Gemini, OpenClaw, Hermes, Cursor)

---

## Installation

### Python CLI (all platforms)

```bash
pip install CiteCheck
```

For PDF support, also install:

```bash
pip install CiteCheck[pdf]
```

Or from source:

```bash
git clone https://github.com/color4-alt/CiteCheck.git
cd CiteCheck
pip install -e ".[pdf,dev]"
```

### Agent Skill Installation

CiteCheck is a cross-agent skill. Install it for your coding agent:

| Agent | Install Location | Command / Method |
|-------|-----------------|------------------|
| **Claude Code** | `~/.claude/skills/citecheck` | Clone or symlink this repo into `~/.claude/skills/citecheck` |
| **Codex CLI** | `~/.codex/skills/citecheck` | Clone or symlink this repo into `~/.codex/skills/citecheck` |
| **OpenClaw** | `~/.openclaw/skills/citecheck` | Clone or symlink this repo into `~/.openclaw/skills/citecheck` |
| **Hermes** | `~/.hermes/skills/citecheck` | Clone or symlink this repo into `~/.hermes/skills/citecheck` |
| **Gemini CLI** | `~/.gemini/skills/citecheck` | Clone or symlink this repo into `~/.gemini/skills/citecheck` |
| **Cursor** | `.cursor/rules/citecheck.mdc` | Copy `skills/citecheck/SKILL.md` content into a `.mdc` rule file |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Append `AGENTS.md` content to your repo instructions |

> **Why no API key is needed for the Skill**: When used as an agent skill, thematic and semantic matching are performed directly by the agent's own LLM reasoning. The CLI handles parsing, format checking, and queryability verification. No external LLM API calls are required.

---

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

---

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
  --api-key API_KEY     Optional: OpenAI API key for LLM-powered matching. Falls back to
                        heuristic rules if omitted. Not required when using CiteCheck as an agent skill.
  -v, --verbose         Verbose output
```

---

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
│ 2. Format Check │  ← Validate BibTeX fields, types, venues
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

**Skill mode**: Steps 1–3 run via CLI; steps 4–5 are performed by the agent directly using its own reasoning.

**Standalone CLI mode**: All steps run via CLI. Step 4–5 use built-in heuristics by default, or external LLM if `--api-key` is provided.

---

## Report Example

The tool generates a Markdown report including:

- **Summary table**: total refs, format issues, verified count, average scores
- **Detailed results table**: per-reference format/queryable/thematic/semantic status
- **Format issues**: specific problems (missing author, wrong entry type, suspicious year, etc.)
- **Queryability results**: verification status from Crossref/Semantic Scholar
- **Uncited references**: entries in `.bib` that are never `\cite{}`'d in the text

See [`examples/example_report.md`](examples/example_report.md) for a sample output.

---

## Project Structure

```
CiteCheck/
├── src/citecheck/             # Python package source
│   ├── __init__.py
│   ├── cli.py                 # Command-line entry point
│   ├── parser.py              # Paper parser (LaTeX / PDF dispatcher)
│   ├── bibtex_parser.py       # BibTeX .bib file parser
│   ├── pdf_parser.py          # PDF text extraction and citation parsing
│   ├── verifier.py            # Crossref / Semantic Scholar API verification
│   ├── matcher.py             # Thematic and semantic scoring (heuristic + LLM)
│   ├── models.py              # Shared dataclasses (Reference, Citation, Paper)
│   └── reporter.py            # Markdown report generator
├── skills/
│   └── citecheck/
│       └── SKILL.md           # Agent skill entry point (cross-platform)
├── .claude-plugin/
│   └── plugin.json            # Claude Code plugin manifest
├── .codex-plugin/
│   └── plugin.json            # Codex CLI plugin manifest
├── CLAUDE.md                  # Project context for Claude Code
├── AGENTS.md                  # Project context for Codex / generic agents
├── GEMINI.md                  # Project context for Gemini CLI
├── references/
│   ├── semantic-matching-prompt.md
│   ├── api-reference.md
│   └── format-check-rules.md
├── scripts/
│   └── check_citations.py     # Standalone script
├── tests/
│   └── test_parser.py
├── examples/
│   └── example_report.md
├── pyproject.toml
├── README.md
└── LICENSE
```

---

## Supported Input Formats

| Format | Priority | Notes |
|--------|----------|-------|
| LaTeX directory | 1st | Requires `.tex` + `.bib`; resolves `\input{}` |
| Single `.tex` file | 2nd | Looks for sibling `.bib` file |
| PDF | Fallback | Extracts text via PyMuPDF; less precise than LaTeX |

---

## API Keys

- **Online verification** uses Crossref and Semantic Scholar public APIs (no key needed, but rate-limited)
- **Semantic matching** uses built-in heuristics by default; for external LLM-powered matching, set `OPENAI_API_KEY` or pass `--api-key`
- **Agent skill mode** requires no API keys — the agent's own reasoning handles matching

---

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

---

## Cross-Agent Compatibility

CiteCheck follows the [agentskills.io](https://agentskills.io) open standard. The skill content in `skills/citecheck/SKILL.md` uses only standard frontmatter fields (`name`, `description`) and agent-agnostic markdown instructions. It is designed to work across:

- Claude Code
- OpenAI Codex CLI
- OpenClaw
- Hermes
- Gemini CLI
- Cursor (via `.mdc` conversion)
- GitHub Copilot (via `AGENTS.md`)

---

## License

MIT License — see [LICENSE](LICENSE).
