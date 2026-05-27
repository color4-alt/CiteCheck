# CiteCheck — Project Context for Claude Code

CiteCheck is a Python CLI tool and agent skill for verifying academic paper citations. This repository contains both the installable Python package (`pip install CiteCheck`) and the agent skill definitions.

## When This Context Applies

Load this context when working on:
- The `citecheck` Python package (`src/citecheck/`)
- The agent skill definitions (`skills/`, `references/`)
- CLI behavior, parsing logic, or report generation
- Bug fixes or feature additions to the citation verification pipeline

## Project Structure

```
CiteCheck/
├── src/citecheck/          # Python package source
│   ├── cli.py              # CLI entry point
│   ├── parser.py           # LaTeX / PDF dispatcher
│   ├── bibtex_parser.py    # BibTeX .bib parser
│   ├── pdf_parser.py       # PDF text extraction
│   ├── verifier.py         # Crossref / Semantic Scholar verification
│   ├── matcher.py          # Thematic & semantic scoring (heuristic + LLM)
│   ├── reporter.py         # Markdown report generator
│   └── models.py           # Shared dataclasses
├── skills/citecheck/       # Agent skill (cross-platform)
│   └── SKILL.md            # Skill entry point
├── references/             # Skill reference docs
│   ├── format-check-rules.md
│   ├── api-reference.md
│   └── semantic-matching-prompt.md
├── scripts/                # Standalone utility scripts
├── tests/                  # pytest suite
├── examples/               # Example outputs
├── pyproject.toml          # Package config
└── README.md               # Human-facing docs
```

## Architecture Decisions

1. **LaTeX-first, PDF-fallback**: `.tex` + `.bib` parsing is precise; PDF extraction is lossy
2. **Skill vs CLI separation**: The CLI handles parsing/format/querying; the agent (Claude) handles thematic/semantic evaluation using its own reasoning
3. **Zero mandatory API keys**: Crossref and Semantic Scholar are public APIs; LLM matching is optional (`--api-key`) or delegated to the agent
4. **Models extracted to `models.py`**: Prevents circular imports between `parser.py`, `bibtex_parser.py`, and `pdf_parser.py`

## Code Style

- Python 3.10+ with type hints
- `pathlib.Path` for all file operations
- Dataclasses for data models (`citecheck.models`)
- Lazy imports in `parser.py` to avoid circular dependencies
- All CLI output uses stderr for diagnostics, stdout for structured data

## Testing

```bash
pip install -e ".[dev]"
pytest tests/
```

## Contributing Notes

- Any change to `skills/citecheck/SKILL.md` must remain **agent-agnostic** (no "Claude"-specific language)
- Skill content should work across Claude Code, Codex, OpenClaw, Hermes, and Gemini CLI
- If adding new CLI flags, update both `cli.py` and `README.md`
