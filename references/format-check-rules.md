# 参考文献格式检查规则

## 通用检查项

### 1. 必填元素完整性
每条参考文献至少应包含：
- [ ] 作者（Author(s)）
- [ ] 标题（Title）
- [ ] 发表年份（Year）
- [ ] 来源（期刊/会议/出版社名）

### 2. 常见格式规范

#### GB/T 7714（中文论文常用）
- 期刊: `[序号] 作者. 题名[J]. 刊名, 年, 卷(期): 起止页码.`
- 会议: `[序号] 作者. 题名[C]//编者. 论文集名. 出版地: 出版者, 年: 起止页码.`
- 专著: `[序号] 作者. 书名[M]. 出版地: 出版者, 年.`

#### APA 7th
- 期刊: `Author, A. A. (Year). Title of article. Title of Periodical, volume(issue), pages. https://doi.org/xxxxx`
- 注意：DOI 格式应为 `https://doi.org/xxxxx`

#### IEEE
- 期刊: `[序号] A. Author, "Title of article," Title of Journal, vol. x, no. x, pp. xxx-xxx, Month Year.`
- 会议: `[序号] A. Author, "Title of paper," in Title of Conference, City, Country, Year, pp. xxx-xxx.`

### 3. 常见错误检查
- [ ] 作者名格式是否统一（全名 vs 缩写）
- [ ] 年份缺失或格式错误（如 `202x` 占位符）
- [ ] 标题大小写是否规范
- [ ] 期刊/会议名是否缩写混乱
- [ ] 页码格式是否统一
- [ ] DOI/URL 是否可访问
- [ ] 标点符号是否统一（中文文献用中文标点，英文用英文标点）

---

## 可查询性检查流程

1. 提取参考文献的标题（优先）或 DOI
2. 使用 Crossref API 查询是否存在
   - 若命中，记录 DOI、作者、年份、期刊
   - 若未命中，尝试 Semantic Scholar API
3. 若两个 API 均未命中：
   - 尝试 Google Scholar（通过 SerpAPI 或 scholarly）
   - 标记为 "查询困难"，在报告中注明
4. 对比返回的作者/年份与原文是否一致
   - 不一致：标记 "信息不匹配"，可能是引用格式错误或引用的是预印本/版本差异
