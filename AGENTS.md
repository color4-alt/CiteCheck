@./skills/citecheck/SKILL.md
@./references/api-reference.md
@./references/format-check-rules.md
@./references/thematic-scoring-prompt.md
@./references/semantic-matching-prompt.md

# CiteCheck — Development & Testing Rules

## Pre-Push Testing Requirement

**Every feature change MUST be validated against the demo test fixtures before committing.**

The `latex_paper/` directory (sibling to `CiteCheck/`) contains intentionally flawed references used as the canonical integration test:

```bash
# From inside CiteCheck/
cd CiteCheck

# 1. Test LaTeX source parsing
citecheck ../latex_paper/main.tex --skip-verification --skip-semantic -o /tmp/test_latex.md

# Expected baseline:
#   - 19 references parsed
#   - 18 citation markers detected
#   - 7 format issues (preprints, wrong entry type, missing author, future year)
#   - Uncited list: only [3] touvron2023llama

# 2. Test PDF fallback parsing
citecheck ../latex_paper/main.pdf --skip-verification --skip-semantic -o /tmp/test_pdf.md

# Expected baseline:
#   - 18 references parsed (PDF loses incomplete entry metadata)
#   - 18 citation markers detected
#   - 0 format issues (PDF parser has limited format checking)
```

### Regression Checklist

- [ ] LaTeX test produces expected reference count (±0)
- [ ] LaTeX test produces expected citation marker count (±0)
- [ ] Uncited references list shows ONLY truly uncited entries (e.g., `touvron2023llama`)
- [ ] PDF test runs without crashing
- [ ] pytest `tests/test_parser.py` passes (8/8)
- [ ] `python -m citecheck --help` works

### Known Improvements (Post-0.1.0)

- **arXiv year parsing** (`pdf_parser.py`): arXiv IDs like `arXiv:2004.05150` are no longer mistaken for publication years.
- **Crossref false-match filtering** (`verifier.py`): Low-similarity matches are now rejected; large year mismatches (>2 years) are flagged separately from small mismatches.

If any baseline metric shifts unexpectedly, investigate before pushing.
