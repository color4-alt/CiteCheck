# Example: LaTeX Paper Citation Verification

## User Request

> "Check the citations in my paper at `./latex_paper/`."

## Agent Workflow

### Step 1 — Parse Paper

```bash
citecheck ./latex_paper/ --skip-verification --skip-semantic -o parsed_report.md
```

**Result**: 19 references extracted, 18 in-text citations detected.

### Step 2 — Format Check

The CLI reports:

| Check | Result |
|-------|--------|
| Required fields | ⚠️ 1 missing venue |
| Year sanity | ⚠️ 1 placeholder year `202x` |
| DOI format | ✅ All valid |

### Step 3 — Queryability Verification

```bash
citecheck ./latex_paper/ --skip-semantic -o verified_report.md
```

**Result**: 17/19 verified via Crossref/Semantic Scholar. 2 marked "unverifiable".

Agent supplements with WebSearch for the 2 unverifiable entries.

### Step 4 — Evaluate Thematic Relevance

Agent evaluates each reference against the paper's title/abstract using the prompt from `references/thematic-scoring-prompt.md`.

**Sample result**:

| Ref | Title | Thematic Score | Reason |
|-----|-------|----------------|--------|
| [3] | Vaswani et al., "Attention Is All You Need" | 0.95 | Directly supports the transformer-based methodology |
| [12] | Smith et al., "Gardening Tips" | 0.10 | Completely unrelated topic |

### Step 5 — Evaluate Semantic Accuracy

Agent extracts citation contexts and compares against cited abstracts using the prompt from `references/semantic-matching-prompt.md`.

**Sample result**:

| Citation | Context | Semantic Score | Reason |
|----------|---------|----------------|--------|
| [3] p.4 | "Following the self-attention mechanism proposed by Vaswani et al..." | 0.90 | Accurately describes the core contribution |
| [7] p.6 | "As shown by Doe et al., accuracy reaches 99%" | 0.40 | Original paper reports 94%, not 99% |

### Step 6 — Output Report

```markdown
## Summary
- Total references: 19
- Format issues: 2
- Query failures: 2
- Average thematic relevance: 0.72
- Average semantic accuracy: 0.81

## Issues
- **High**: Ref [12] appears completely off-topic (thematic 0.10)
- **High**: Ref [7] contains a factual misquote (semantic 0.40)
- **Medium**: Ref [5] has placeholder year `202x`
- **Low**: Ref [9] missing venue field
```
