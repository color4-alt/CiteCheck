---
name: citecheck
description: Use when the user asks to "verify citations", "check references", "validate paper citations", or "evaluate reference relevance". It extracts references from LaTeX/PDF papers, checks formatting rules, verifies existence via Crossref/Semantic Scholar APIs, and scores thematic/semantic relevance.
---

# CiteCheck — Paper Citation Verification

## Overview

CiteCheck verifies academic paper citations by combining structured parsing with agent-native LLM evaluation. It supports LaTeX source files (preferred) and PDF fallback.

## Workflow

1. **Parse paper**: Call `citecheck` CLI to read LaTeX (preferred) or PDF, extract references and body text
2. **Format check**: Call `citecheck` CLI to validate bibliography entries
3. **Queryability verification**: Call `citecheck` CLI to verify existence via Crossref / Semantic Scholar
4. **Thematic relevance scoring**: **Evaluated by the agent directly** — compare cited paper title/abstract/venue against the citing paper
5. **Semantic accuracy scoring**: **Evaluated by the agent directly** — compare in-text citation context against cited source content
6. **Generate report**: Aggregate all results into a Markdown report

> **Why matching steps are not done by the CLI**
> The `citecheck` CLI can run standalone with optional `--api-key` for external LLM-powered matching. When used as a Skill, the host agent itself possesses LLM reasoning capabilities. Direct evaluation is faster, more consistent, and **requires no additional API keys from the user**.

---

## 1. Parse Paper (CLI)

### LaTeX source (preferred)

```bash
citecheck path/to/latex_project/ --skip-verification --skip-semantic -o parsed_report.md
```

Or parse a single file:

```bash
citecheck main.tex --skip-verification --skip-semantic -o parsed_report.md
```

### PDF (fallback)

```bash
citecheck paper.pdf --skip-verification --skip-semantic -o parsed_report.md
```

> `--skip-verification` and `--skip-semantic` are required in Skill mode because steps 3–5 are performed directly by the agent.

---

## 2. Format Check (CLI)

The CLI automatically checks and reports format issues:

| Check item | Description |
|------------|-------------|
| Required fields | Author, title, year, venue completeness |
| Format consistency | Punctuation, capitalization, abbreviation uniformity |
| DOI/URL | If present, whether format is correct and accessible |
| Year sanity | No `202x` placeholders, not in the future |

Detailed rules: see [../../references/format-check-rules.md](../../references/format-check-rules.md).

---

## 3. Queryability Verification (CLI + Agent Supplement)

The `citecheck` CLI attempts to call Crossref and Semantic Scholar public APIs to verify citation existence.

**If the CLI fails due to network/SSL issues**, the agent should use WebSearch to directly query suspicious citations (especially those marked "unverifiable"), supplementing the verification results.

---

## 4. Thematic Relevance Scoring (Agent Direct Evaluation)

**Do not call the CLI or any external API.** Use the agent's own reasoning capabilities.

For each reference, extract:
- Citing paper: `title`, `abstract`, `keywords`
- Cited paper: `title`, `abstract` (from API results or WebSearch), `venue`

Evaluate using this prompt framework:

```
请评估以下两篇论文的主题匹配度。

【论文 A（本文）】
标题：{paper_title}
摘要：{paper_abstract}
关键词：{paper_keywords}

【论文 B（引文）】
标题：{cited_title}
摘要：{cited_abstract}
来源：{cited_venue}

【评分标准】
- 1.0：高度相关（同一细分领域，直接支撑本文论点）
- 0.7：相关（同一领域，间接相关）
- 0.4：弱相关（同一大学科，但关联有限）
- 0.1：几乎无关
- 0.0：完全无关

请给出 0.0-1.0 的评分，并用一句话说明理由。
```

---

## 5. Semantic Accuracy Scoring (Agent Direct Evaluation)

**Do not call the CLI or any external API.** Use the agent's own reasoning capabilities.

For each in-text citation position:

1. Extract 1–2 sentences before and after the citation marker as `citing_text`
2. Obtain the cited paper's abstract via Semantic Scholar or WebSearch as `cited_text`
3. Evaluate semantic consistency using:

```
【评分标准】
- 1.0：语义完全一致（引用内容准确反映了原文）
- 0.8：高度一致（核心含义匹配，细节略有差异）
- 0.5：部分相关（同一主题，但引用对原文有过度推断或断章取义）
- 0.2：弱相关（勉强沾边）
- 0.0：无关或矛盾（引用内容与原文相悖）

Text A（引用上下文）：{citing_text}
Text B（引文摘要）：{cited_text}

请给出 0.0-1.0 的评分，并用一句话说明理由。
```

Detailed prompt template: see [../../references/semantic-matching-prompt.md](../../references/semantic-matching-prompt.md).

---

## 6. Output Report

Generate a Markdown report containing:

### Summary
- Total references
- Format issues count
- Query failures / suspicious count
- Average thematic relevance score
- Average semantic accuracy score

### Detailed Results Table

| No. | Title | Format | Queryable | Thematic | Semantic | Notes |
|-----|-------|--------|-----------|----------|----------|-------|
| 1 | ... | ✅/⚠️/❌ | ✅/❌ | 0.85 | 0.90 | DOI mismatch |

### Issue Summary
- List all findings and recommendations by severity

---

## Dependencies

```bash
pip install CiteCheck
```

For PDF support:

```bash
pip install CiteCheck[pdf]
```

---

## Notes

- **No `--api-key` is required in Skill mode**. Thematic and semantic matching are performed directly by the agent, with no external LLM API calls.
- Prioritize LaTeX source files; parsing accuracy is far higher than PDF.
- Add delays and retries to API calls to avoid rate limiting.
- When Semantic Scholar abstracts are missing, fall back to Crossref + title keywords.
- Semantic matching requires the cited paper's abstract; mark "source unreachable" when unavailable.
- If placeholder citations like `=?` or `[?, ?]` are found, mark them as "unverifiable references".
