---
name: CiteCheck
description: This skill should be used when the user asks to "verify citations", "check references", "validate paper citations", or "evaluate reference relevance". It extracts references from LaTeX/PDF papers, checks formatting rules, verifies existence via Crossref/Semantic Scholar APIs, and scores thematic/semantic relevance.
---

# 论文引用检查

## 工作流程

1. **解析论文**：读取 LaTeX 源文件（优先）或 PDF，提取参考文献列表和正文内容
2. **格式检查**：逐项验证参考文献格式，检查必填元素
3. **可查询性验证**：通过 Crossref / Semantic Scholar / Google Scholar 验证引文存在性
4. **主题匹配度评分**：对比引文与本文的标题、摘要、关键词相关性
5. **语义匹配度评分**：对比正文中引用内容与引文原文的语义一致性
6. **生成报告**：输出 Markdown 表格/文本报告

## 1. 论文解析

### LaTeX 源文件（优先）

```python
# 提取 .bib 文件和 .tex 正文
import glob, os

bib_files = glob.glob("*.bib")
tex_files = glob.glob("*.tex")

# 用 bibtexparser 解析 .bib
import bibtexparser
with open(bib_files[0]) as f:
    bib_db = bibtexparser.load(f)
refs = bib_db.entries  # list of dicts with author, title, year, etc.

# 从 .tex 提取正文和 \cite{...} 标记
with open(tex_files[0]) as f:
    tex_content = f.read()
# 移除注释和数学环境后提取 \cite{key} 及其上下文
```

### PDF（降级方案）

```python
import pdfplumber

with pdfplumber.open("paper.pdf") as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages)

# 定位 "References" / "参考文献" 章节，提取列表
# 用正则匹配编号或作者-年份格式的条目
```

**PDF 提取失败时**：尝试 `pymupdf` 或 `pdftotext` 作为备选。

## 2. 格式检查

对每条参考文献检查：

| 检查项 | 说明 |
|--------|------|
| 必填元素 | 作者、标题、年份、来源是否齐全 |
| 格式一致性 | 标点、大小写、缩写是否统一 |
| DOI/URL | 如有，是否格式正确且可访问 |
| 年份合理性 | 非 `202x` 占位符，不晚于当前年 |

详细规则见 [references/format-check-rules.md](references/format-check-rules.md)。

## 3. 可查询性验证

按优先级调用 API，验证引文是否真实存在：

```python
import requests, urllib.parse

def query_crossref(title):
    url = f"https://api.crossref.org/works?query.title={urllib.parse.quote(title)}&rows=3&mailto=your@email.com"
    r = requests.get(url, timeout=15)
    return r.json()["message"]["items"]

def query_semantic_scholar(title):
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(title)}&fields=title,authors,year,abstract,fieldsOfStudy&limit=3"
    r = requests.get(url, timeout=15)
    return r.json()["data"]
```

- **命中**：记录 DOI、作者、年份、期刊，与原文比对
- **未命中**：降级到下一个 API；全部失败则标记 "查询困难"

API 详情见 [references/api-reference.md](references/api-reference.md)。

## 4. 主题匹配度评分

提取本文信息：`title`、`abstract`、`keywords`。

对每条引文，提取其 `title`、`abstract`（从 API 获取）、`fieldsOfStudy`。

使用 LLM 评估两者主题相关性，Prompt：

```
请评估以下两篇论文的主题匹配度。

【论文 A（本文）】
标题：{paper_title}
摘要：{paper_abstract}
关键词：{paper_keywords}

【论文 B（引文）】
标题：{cited_title}
摘要：{cited_abstract}
关键词：{cited_keywords}

【评分标准】
- 1.0：高度相关（同一细分领域，直接支撑本文论点）
- 0.7：相关（同一领域，间接相关）
- 0.4：弱相关（同一大学科，但关联有限）
- 0.1：几乎无关
- 0.0：完全无关

请给出 0.0-1.0 的评分，并用一句话说明理由。
```

## 5. 语义匹配度评分

对正文中每个引用位置：

1. 提取引用标记前后 1-2 句话作为 `citing_text`
2. 通过 API 获取引文全文（优先 Semantic Scholar 的 `abstract`，若需要全文本则尝试 open-access PDF）
3. 在引文中定位最相关的段落作为 `cited_text`
4. 使用 [references/semantic-matching-prompt.md](references/semantic-matching-prompt.md) 中的 Prompt 调用 LLM 评分

## 6. 输出报告

生成 Markdown 报告，包含以下表格：

### 摘要
- 总参考文献数
- 格式问题数
- 查询失败数
- 主题匹配度平均分
- 语义匹配度平均分

### 详细检查结果表

| 序号 | 标题 | 格式检查 | 可查询性 | 主题匹配度 | 语义匹配度 | 备注 |
|------|------|----------|----------|------------|------------|------|
| 1 | ... | ✅/⚠️/❌ | ✅/❌ | 0.85 | 0.90 | DOI 不一致 |

### 问题汇总
- 按严重程度列出所有发现的问题和建议

## 依赖

```bash
pip install bibtexparser pdfplumber pymupdf requests
```

## 注意事项

- 优先处理 LaTeX 源文件，解析精度远高于 PDF
- API 调用需加延时和重试，避免触发限流
- Semantic Scholar 摘要缺失时，用 Crossref + 标题关键词做降级匹配
- 语义匹配需要引文全文，open-access 论文优先；无法获取全文时标记 "原文不可达"
