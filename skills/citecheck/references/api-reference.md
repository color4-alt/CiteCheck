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

## OpenAlex API

### 基础信息
- **API 地址**: `https://api.openalex.org/works`
- **文档**: https://docs.openalex.org/
- **限制**: 完全开放，无需 API Key，建议添加 `mailto` 以进入 polite pool

### 常用查询方式

#### 按标题搜索
```
GET https://api.openalex.org/works?search={encoded_title}&per-page=5
```

#### 按 DOI 查询
```
GET https://api.openalex.org/works/doi:{doi}
```

### 返回字段（常用）
- `results[].display_name` - 论文标题
- `results[].publication_year` - 发表年份
- `results[].host_venue.display_name` - 期刊/会议名
- `results[].doi` - DOI
- `results[].abstract_inverted_index` - 倒排索引形式的摘要（需重建）
- `results[].cited_by_count` - 被引次数

---

## PubMed (E-utilities)

### 基础信息
- **API 地址**: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`
- **文档**: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- **限制**: 无 API Key，建议添加 `tool` 和 `email` 参数

### 常用查询方式

#### 搜索 PMIDs
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={encoded_title}&retmax=5&retmode=json
```

#### 获取文献详情
```
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json
```

### 返回字段（常用）
- `result.{pmid}.title` - 论文标题
- `result.{pmid}.pubdate` - 发表日期（通常格式为 "YYYY Mon"）
- `result.{pmid}.fulljournalname` - 期刊全名
- `result.{pmid}.articleids[]` - 包含 DOI（`idtype: "doi"`）

---

## arXiv API

### 基础信息
- **API 地址**: `http://export.arxiv.org/api/query`
- **文档**: https://info.arxiv.org/help/api/index.html
- **限制**: 完全开放，需遵守速率限制（建议间隔 3 秒）

### 常用查询方式

#### 按标题搜索
```
GET http://export.arxiv.org/api/query?search_query=ti:{encoded_title}&max_results=5&sortBy=relevance
```

#### 按 arXiv ID 查询
```
GET http://export.arxiv.org/api/query?id_list={arxiv_id}
```

### 返回格式
Atom XML，字段包括：
- `entry/title` - 论文标题
- `entry/published` - 发表日期
- `entry/author/name` - 作者名
- `entry/id` - arXiv URL（ID 为最后一段）
- `entry/link[@title="doi"]` - DOI（如存在）
- `entry/summary` - 摘要

---

## dblp API

### 基础信息
- **API 地址**: `https://dblp.org/search/publ/api`
- **文档**: https://dblp.org/faq/How+to+use+the+dblp+search+API.html
- **限制**: 完全开放，无需 API Key

### 常用查询方式

#### 按标题搜索
```
GET https://dblp.org/search/publ/api?q={encoded_title}&format=json&h=5
```

### 返回字段（常用）
- `result.hits.hit[].info.title` - 论文标题
- `result.hits.hit[].info.year` - 发表年份
- `result.hits.hit[].info.venue` - 期刊/会议名
- `result.hits.hit[].info.doi` - DOI
- `result.hits.hit[].info.authors.author[]` - 作者列表

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
3. 第三选 OpenAlex（开放图谱，覆盖广）
4. PubMed / arXiv / dblp 作为领域补充
5. Google Scholar 作为兜底（覆盖面广，但需额外工具）
