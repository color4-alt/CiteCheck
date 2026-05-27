# Citation Check Report

**Paper**: TEVA: Type-Aware Evidence Verification and Aggregation for BioASQ Phase B without Backbone Retraining  
**Check Date**: 2026-05-27  
**Source Type**: latex  
**Total References**: 10  
**Citations in Text**: 8

## Summary

| Metric | Result |
|--------|--------|
| Total References | 10 |
| Format Issues | 4 |
| Online Verified | 9/10 |
| Avg Thematic Relevance | 0.77 |
| Avg Semantic Accuracy | 0.86 |

## Detailed Results

| No. | Title | Format | Queryable | Thematic | Semantic | Notes |
|-----|-------|--------|-----------|----------|----------|-------|
| 1 | SciBERT: A pretrained language model for scientific text | ✅ | ✅ | 0.70 | 0.85 | OK |
| 2 | Language models are few-shot learners | ✅ | ✅ | 0.40 | 0.90 | OK |
| 3 | Domain-specific language model pretraining for biomedical NLP | ✅ | ✅ | 0.80 | 0.90 | Missing DOI/URL |
| 4 | BioASQ-QA: A manually curated corpus for Biomedical QA | ⚠️ | ✅ | 1.00 | 0.80 | Preprint source: bioRxiv; Year mismatch: ref=2022, found=2023 |
| 5 | BioMistral: A Collection of Open-Source Pretrained LLMs for Medical Domains | ✅ | ✅ | 1.00 | 0.90 | Missing DOI/URL; Preprint source: arXiv preprint arXiv:2402.10373 |
| 6 | BioBERT: a pre-trained biomedical language representation model | ✅ | ✅ | 0.80 | 0.90 | Missing DOI/URL |
| 7 | Large language models encode clinical knowledge | ✅ | ✅ | 0.50 | 0.75 | Missing DOI/URL |
| 8 | An overview of the BIOASQ large-scale biomedical semantic indexing and question answering competition | ⚠️ | ✅ | 1.00 | 0.90 | Should be @article, not @inproceedings (venue is a journal); Missing DOI/URL |
| 9 | Chain-of-thought prompting elicits reasoning in large language models | ✅ | ✅ | 0.50 | 0.85 | Missing DOI/URL |
| 10 | Llama 2: Open Foundation and Fine-Tuned Chat Models | ✅ | ✅ | — | — | Missing DOI/URL; Preprint source: arXiv preprint arXiv:2307.09288 |

## 1. Format Check Details

### [4] BioASQ-QA: A manually curated corpus for Biomedical Question Answering
- ⚠️ Preprint source: bioRxiv
- ⚠️ Year mismatch: ref=2022, found=2023

**Suggested fix:**
```bibtex
@article{krithara2023bioasq,
  title={BioASQ-QA: A manually curated corpus for Biomedical Question Answering},
  author={Krithara, Anastasia and Nentidis, Anastasios and Bougiatiotis, Konstantinos and Paliouras, Georgios},
  journal={Scientific Data},
  volume={10},
  pages={170},
  year={2023},
  doi={10.1038/s41597-023-02068-4}
}
```

### [8] An overview of the BIOASQ large-scale biomedical semantic indexing and question answering competition
- ⚠️ Should be @article, not @inproceedings (venue is a journal)
- ⚠️ Missing DOI/URL

**Suggested fix:**
```bibtex
@article{tsatsaronis2015overview,
  title={An overview of the BIOASQ large-scale biomedical semantic indexing and question answering competition},
  author={Tsatsaronis, George and Balikas, Georgios and Malakasiotis, Prodromos and others},
  journal={BMC Bioinformatics},
  volume={16},
  pages={138},
  year={2015},
  doi={10.1186/s12859-015-0564-6}
}
```

## 2. Queryability Verification

- **[1]** ✅ Found via Crossref: "SciBERT: A pretrained language model for sci..." (2019)
- **[2]** ✅ Found via Crossref: "Language Models are Few-Shot Learners" (2020)
- **[3]** ✅ Found via Crossref: "Domain-specific language model pretraining for..." (2021)
- **[4]** ✅ Found via Crossref: "BioASQ-QA: A manually curated corpus for Biom..." (2023)
- **[5]** ✅ Found via SemanticScholar: "BioMistral: A Collection of Open-Source Pretr..." (2024)
- **[6]** ✅ Found via Crossref: "BioBERT: a pre-trained biomedical language rep..." (2020)
- **[7]** ✅ Found via Crossref: "Large language models encode clinical knowledg..." (2023)
- **[8]** ✅ Found via Crossref: "An overview of the BIOASQ large-scale biomed..." (2015)
- **[9]** ✅ Found via SemanticScholar: "Chain-of-thought prompting elicits reasoning ..." (2022)
- **[10]** ✅ Found via SemanticScholar: "Llama 2: Open Foundation and Fine-Tuned Chat..." (2023)

## 3. Thematic Relevance

| No. | Score | Reason |
|-----|-------|--------|
| 1 | 0.70 | Scientific text pretraining; relevant to biomedical NLP but not directly to QA |
| 2 | 0.40 | General LLM background; weak direct connection to biomedical QA |
| 3 | 0.80 | Domain-specific biomedical pretraining; directly relevant to biomedical NLP |
| 4 | 1.00 | Core dataset used in experiments; directly supports the work |
| 5 | 1.00 | Backbone model used in the paper; directly central to the method |
| 6 | 0.80 | Foundational biomedical LM; relevant to the domain |
| 7 | 0.50 | Medical LLM general research; weaker connection to BioASQ QA |
| 8 | 1.00 | Core benchmark; the entire paper is built on this competition |
| 9 | 0.50 | Prompting/reasoning method; partially relevant to inference-time control |

## 4. Semantic Accuracy

| Citation | Score | Reason |
|----------|-------|--------|
| [1] | 0.85 | Title keywords directly mentioned in context |
| [2] | 0.90 | Title keywords directly mentioned in context |
| [3] | 0.90 | Title keywords directly mentioned in context |
| [4] | 0.80 | Title keywords directly mentioned in context |
| [5] | 0.90 | Title keywords directly mentioned in context |
| [6] | 0.90 | Title keywords directly mentioned in context |
| [7] | 0.75 | Title keywords directly mentioned in context |
| [8] | 0.90 | Title keywords directly mentioned in context |
| [9] | 0.85 | Title keywords directly mentioned in context |

## 5. Uncited References

- **[10]** `touvron2023llama` — Llama 2: Open Foundation and Fine-Tuned Chat Models

---
*Generated by CiteCheck*
