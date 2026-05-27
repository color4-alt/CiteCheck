---
name: CiteCheck
description: This skill should be used when the user asks to "verify citations", "check references", "validate paper citations", or "evaluate reference relevance". It extracts references from LaTeX/PDF papers, checks formatting rules, verifies existence via Crossref/Semantic Scholar APIs, and scores thematic/semantic relevance.
---

# 论文引用检查

## 工作流程

1. **解析论文**：调用 `citecheck` CLI 读取 LaTeX 源文件（优先）或 PDF，提取参考文献列表和正文内容
2. **格式检查**：调用 `citecheck` CLI 逐项验证参考文献格式
3. **可查询性验证**：调用 `citecheck` CLI 通过 Crossref / Semantic Scholar 验证引文存在性
4. **主题匹配度评分**：**由 Claude 直接评估**——对比引文与本文的标题、摘要、关键词相关性
5. **语义匹配度评分**：**由 Claude 直接评估**——对比正文中引用内容与引文原文的语义一致性
6. **生成报告**：汇总所有结果，输出 Markdown 报告

> **为什么匹配步骤不由 CLI 完成？**
> `citecheck` CLI 可作为独立工具运行（此时可选 `--api-key` 接入外部 LLM）。但作为 Skill 使用时，Claude 自身具备 LLM 推理能力，直接评估比调用外部 API 更快速、更一致，且**不需要用户准备任何 API key**。

---

## 1. 解析论文（CLI）

### LaTeX 源文件（优先）

```bash
citecheck path/to/latex_project/ --skip-verification --skip-semantic -o parsed_report.md
```

或解析单文件：

```bash
citecheck main.tex --skip-verification --skip-semantic -o parsed_report.md
```

### PDF（降级方案）

```bash
citecheck paper.pdf --skip-verification --skip-semantic -o parsed_report.md
```

> `--skip-verification` 和 `--skip-semantic` 在 Skill 模式下是必需的，因为步骤 3–5 由 Claude 直接完成。

---

## 2. 格式检查（CLI）

`citecheck` 会自动检查并输出格式问题：

| 检查项 | 说明 |
|--------|------|
| 必填元素 | 作者、标题、年份、来源是否齐全 |
| 格式一致性 | 标点、大小写、缩写是否统一 |
| DOI/URL | 如有，是否格式正确且可访问 |
| 年份合理性 | 非 `202x` 占位符，不晚于当前年 |

详细规则见 [references/format-check-rules.md](references/format-check-rules.md)。

---

## 3. 可查询性验证（CLI + Claude 补充）

`citecheck` CLI 会尝试调用 Crossref 和 Semantic Scholar 公共 API 验证引文存在性。

**若 CLI 因网络/SSL 问题无法完成验证**，Claude 应通过 WebSearch 直接查询可疑引文（特别是标记为 "查询困难" 的条目），补充验证结果。

---

## 4. 主题匹配度评分（Claude 直接评估）

**不调用 CLI，也不调用外部 API。** 使用 Claude 自身的推理能力完成。

对每条引文，提取：
- 本文信息：`title`、`abstract`、`keywords`
- 引文信息：`title`、`abstract`（从步骤 3 的 API 结果或 WebSearch 获取）、`venue`

按以下 Prompt 框架逐条评估：

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

## 5. 语义匹配度评分（Claude 直接评估）

**不调用 CLI，也不调用外部 API。** 使用 Claude 自身的推理能力完成。

对正文中每个引用位置：

1. 提取引用标记前后 1-2 句话作为 `citing_text`
2. 通过 Semantic Scholar 或 WebSearch 获取引文摘要作为 `cited_text`
3. 使用以下 Prompt 评估语义一致性：

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

详细 Prompt 模板见 [references/semantic-matching-prompt.md](references/semantic-matching-prompt.md)。

---

## 6. 输出报告

生成 Markdown 报告，包含以下表格：

### 摘要
- 总参考文献数
- 格式问题数
- 查询失败/可疑数
- 主题匹配度平均分
- 语义匹配度平均分

### 详细检查结果表

| 序号 | 标题 | 格式检查 | 可查询性 | 主题匹配度 | 语义匹配度 | 备注 |
|------|------|----------|----------|------------|------------|------|
| 1 | ... | ✅/⚠️/❌ | ✅/❌ | 0.85 | 0.90 | DOI 不一致 |

### 问题汇总
- 按严重程度列出所有发现的问题和建议

---

## 依赖

```bash
pip install CiteCheck
```

如需 PDF 支持：

```bash
pip install CiteCheck[pdf]
```

---

## 注意事项

- **Skill 模式下不需要 `--api-key`**。主题匹配和语义匹配由 Claude 直接完成，无需外部 LLM API。
- 优先处理 LaTeX 源文件，解析精度远高于 PDF。
- API 调用需加延时和重试，避免触发限流。
- Semantic Scholar 摘要缺失时，用 Crossref + 标题关键词做降级匹配。
- 语义匹配需要引文摘要；无法获取时标记 "原文不可达"。
- 若发现 `=?` 或 `[?, ?]` 等占位符引用，应标记为 "不可验证引用"。
