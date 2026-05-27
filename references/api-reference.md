# 引文查询 API 参考

## Crossref API

### 基础信息
- **API 地址**: `https://api.crossref.org/works`
- **文档**: https://api.crossref.org/swagger-ui/index.html
- **限制**:  polite pool 需添加 `mailto` 参数

### 常用查询方式

#### 按 DOI 查询
```
GET https://api.crossref.org/works/{doi}
```

#### 按标题查询
```
GET https://api.crossref.org/works?query.title={encoded_title}&rows=5
```

#### 按作者+标题查询
```
GET https://api.crossref.org/works?query.author={author}&query.title={title}&rows=5
```

### 返回字段（常用）
- `message.title[0]` - 论文标题
- `message.author[]` - 作者列表（含 `given`, `family`）
- `message.published-print` / `message.published-online` - 发表日期
- `message.DOI` - DOI
- `message.container-title[0]` - 期刊/会议名
- `message.type` - 文献类型（journal-article, proceedings-article 等）

---

## Semantic Scholar API

### 基础信息
- **API 地址**: `https://api.semanticscholar.org/graph/v1`
- **文档**: https://api.semanticscholar.org/api-docs/
- **限制**: 免费版 100 requests/5min，无需 API Key

### 常用查询方式

#### 按标题搜索
```
GET https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_title}&fields=title,authors,year,abstract,fieldsOfStudy&limit=5
```

#### 按 Paper ID 获取详情
```
GET https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields=title,authors,year,abstract,fieldsOfStudy,citationCount
```

#### 按 Corpus ID 或 DOI 查询
```
GET https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,abstract,year
```

### 返回字段（常用）
- `title` - 论文标题
- `authors[].name` - 作者名
- `year` - 发表年份
- `abstract` - 摘要
- `fieldsOfStudy` - 研究领域
- `citationCount` - 被引次数
- `paperId` - Semantic Scholar 内部 ID

---

## Google Scholar

### 说明
Google Scholar 没有官方 API。如需使用：

1. **SerpAPI**（第三方服务，需 API Key）
   - 地址: `https://serpapi.com/search.json?engine=google_scholar&q={query}&api_key={key}`

2. **scholarly**（Python 库，有反爬限制）
   - `pip install scholarly`
   - 使用代理池或延时请求避免被封

### 建议优先级
1. 首选 Crossref（开放、稳定、权威）
2. 次选 Semantic Scholar（开放 API，含摘要）
3. Google Scholar 作为补充（覆盖面广，但需额外工具）
