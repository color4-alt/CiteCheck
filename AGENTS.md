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

---

## Pre-Push Skill End-to-End Test

**Before every push, run a full skill integration test in a clean agent environment.**

This validates that the skill installs correctly, triggers properly, and produces correct output when invoked by the agent.

### Test Steps

```bash
# 1. Start a fresh agent session with no memory of previous interactions
#    (In Kimi CLI: open a new terminal or use /reset to clear context)

# 2. Uninstall the previous citecheck skill
rm -rf ~/.claude/skills/citecheck
rm -rf ~/.kimi/skills/citecheck

# 3. Install the new skill from the local repository
cp -r /path/to/CiteCheck/skills/citecheck ~/.kimi/skills/citecheck
#    (Adjust path for your agent: ~/.claude/skills/, ~/.kimi/skills/, etc.)

# 4. Trigger the skill via natural language
#    Ask the agent: "Check the citations in this paper"
#    Provide a sample PDF or LaTeX file (e.g., error_test/2605.00061v1.pdf)

# 5. Review the generated report for obvious defects:
#    - ArXiv references showing year mismatch (e.g., 1904, 2004, 2010)
#    - Crossref returning completely wrong papers (e.g., 1990 → 2020)
#    - Missing references (should be 0 for well-formed papers)
#    - Format errors that shouldn't exist
#    - Empty ref_indices or uncited false positives

# 6. If defects are found:
#    a. Identify the root cause (parser, verifier, or skill logic)
#    b. Fix the code
#    c. Re-run steps 2–5
#    d. DO NOT push until the report is clean

# 7. Only push after the report passes inspection
```

### Defect Criteria (Block Push)

The following issues in the skill-generated report **must** be resolved before pushing:

- [ ] **ArXiv year errors**: Any arXiv reference with year derived from the arXiv ID (e.g., `1904`, `2004`, `2010` instead of actual publication year)
- [ ] **Crossref false matches**: Year mismatch > 5 years on a well-known paper (e.g., Elman 1990 returning 2020)
- [ ] **Missing references**: References that clearly exist but are marked "Not found"
- [ ] **Parser crashes**: PDF or LaTeX parsing throws exceptions
- [ ] **Skill trigger failure**: Agent fails to recognize or invoke the skill

### Rollback Procedure

If defects are discovered after commit but before push:

```bash
# Revert the faulty commit
git revert HEAD

# Or reset to last known good state
git reset --hard <last-good-commit>

# Fix the issue, then re-run the full test suite
```

If defects are discovered **after** push:

1. Immediately create a hotfix branch
2. Revert the problematic change on `main`
3. Fix and re-test in the hotfix branch
4. Open a PR for review before merging

---

If any baseline metric shifts unexpectedly, investigate before pushing.
