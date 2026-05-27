# Example: PDF Paper Citation Verification (Fallback)

## User Request

> "I only have the PDF of my paper. Can you check the citations?"

## Agent Workflow

### Step 1 — Parse Paper

```bash
citecheck paper.pdf --skip-verification --skip-semantic -o parsed_report.md
```

**Result**: 18 references extracted (PDF parsing is lossy compared to LaTeX), 18 in-text citations detected.

> **Note**: PDF parsing heuristically splits plain text into author/title/venue/year fields. Accuracy is lower than LaTeX source parsing. Always prefer LaTeX when available.

### Step 2 — Format Check

The CLI reports:

| Check | Result |
|-------|--------|
| Required fields | ⚠️ 3 fields unclear due to PDF extraction noise |
| Year sanity | ✅ All valid |
| DOI format | ⚠️ 1 malformed (line break inserted by PDF) |

### Step 3 — Queryability Verification

```bash
citecheck paper.pdf --skip-semantic -o verified_report.md
```

**Result**: 15/18 verified via Crossref/Semantic Scholar. 3 marked "unverifiable".

Agent uses WebSearch to supplement:
- One reference had OCR noise in the title (`Neural Netw0rks` → corrected to `Neural Networks`)
- Two references were successfully verified via Google Scholar after manual title correction

### Step 4 — Evaluate Thematic Relevance

Agent evaluates each reference against the paper's title/abstract.

**Sample result**:

| Ref | Extracted Title | Thematic Score | Reason |
|-----|-----------------|----------------|--------|
| [5] | "BERT: Pre-training..." | 0.90 | Core related work for the NLP methodology |
| [14] | "Cooking with Deep Learning" | 0.15 | Off-topic; likely a parsing error or spurious match |

### Step 5 — Evaluate Semantic Accuracy

Agent extracts citation contexts and compares against cited abstracts.

**Sample result**:

| Citation | Context | Semantic Score | Reason |
|----------|---------|----------------|--------|
| [5] p.3 | "BERT introduced the masked language modeling objective..." | 0.85 | Correctly paraphrases the original contribution |
| [11] p.7 | "ResNet achieved 3.57% top-5 error on ImageNet" | 0.60 | Correct statistic, but cited as top-1 error in context |

### Step 6 — Output Report

```markdown
## Summary
- Total references: 18
- Format issues: 4
- Query failures: 3 (1 resolved via WebSearch)
- Average thematic relevance: 0.68
- Average semantic accuracy: 0.74

## Issues
- **High**: Ref [14] is off-topic or malformed (thematic 0.15)
- **High**: Ref [11] misrepresents metric scope (semantic 0.60)
- **Medium**: 3 references had PDF extraction noise affecting verification
- **Low**: Ref [8] DOI contains line-break artifact

## Recommendations
- Prefer LaTeX source for future checks to avoid PDF extraction noise.
```
