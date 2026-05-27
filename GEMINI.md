@./skills/citecheck/SKILL.md
@./references/api-reference.md
@./references/format-check-rules.md
@./references/semantic-matching-prompt.md

# Gemini-Specific Notes

When using CiteCheck with Gemini CLI:

- Install the Python package: `pip install CiteCheck`
- For PDF support: `pip install CiteCheck[pdf]`
- The `citecheck` CLI handles parsing, format checking, and queryability verification
- Thematic and semantic relevance scoring should be performed directly by Gemini using the prompt templates in `references/semantic-matching-prompt.md`
- No OpenAI API key is required; Gemini's own reasoning capabilities are sufficient for the matching steps
