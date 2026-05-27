# 主题相关性评估 Prompt

## 用途

评估引用论文（引文）与当前论文（本文）之间的主题匹配度。

## Prompt 模板

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

## 使用说明

1. 提取本文的 `title`、`abstract`、`keywords`
2. 提取引文的 `title`、`abstract`（来自 API 结果或 WebSearch）、`venue`
3. 将信息填入模板，调用 LLM 评估
4. 记录评分和理由，用于最终报告

## 注意事项

- 如果引文摘要不可获取，标记为 "source unreachable"
- 如果引文为预印本，venue 可标记为 "preprint"
- 评分应基于内容主题而非引用频率或作者知名度
