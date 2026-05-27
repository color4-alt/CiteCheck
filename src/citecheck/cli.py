"""Command-line interface for citation checker."""

import argparse
import sys
from pathlib import Path

from citecheck.parser import PaperParser
from citecheck.verifier import CitationVerifier
from citecheck.matcher import ThematicMatcher, SemanticMatcher
from citecheck.reporter import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Check citations in academic papers (PDF or LaTeX)."
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to the paper file (PDF, .tex, or directory with .tex + .bib)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="citation_check_report.md",
        help="Output report path (default: citation_check_report.md)",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip online verification (Crossref/Semantic Scholar/WebSearch)",
    )
    parser.add_argument(
        "--skip-semantic",
        action="store_true",
        help="Skip semantic matching (requires LLM API)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API key for semantic matching (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Step 1: Parse paper
    print("[1/5] Parsing paper...")
    paper_parser = PaperParser()
    paper = paper_parser.parse(input_path)
    print(f"      Found {len(paper.references)} references, {len(paper.citations)} citation markers")

    # Step 2: Format check
    print("[2/5] Checking format...")
    verifier = CitationVerifier(skip_online=args.skip_verification)
    format_results = verifier.check_format(paper.references)
    issue_count = sum(1 for r in format_results if r.issues)
    print(f"      {issue_count} format issues found")

    # Step 3: Queryability
    print("[3/5] Verifying queryability...")
    if args.skip_verification:
        print("      Skipped (use --skip-verification to enable)")
        query_results = []
    else:
        query_results = verifier.verify_queryability(paper.references)
        found = sum(1 for r in query_results if r.found)
        print(f"      {found}/{len(paper.references)} verified online")

    # Step 4: Matching
    print("[4/5] Evaluating relevance...")
    thematic_results = ThematicMatcher().evaluate(paper)
    avg_thematic = sum(r.score for r in thematic_results) / len(thematic_results) if thematic_results else 0
    print(f"      Thematic relevance avg: {avg_thematic:.2f}")

    if not args.skip_semantic and paper.citations:
        semantic_results = SemanticMatcher(api_key=args.api_key).evaluate(paper)
        avg_semantic = sum(r.score for r in semantic_results) / len(semantic_results) if semantic_results else 0
        print(f"      Semantic accuracy avg: {avg_semantic:.2f}")
    else:
        semantic_results = []
        if args.skip_semantic:
            print("      Semantic matching skipped")
        else:
            print("      No citation markers found for semantic matching")

    # Step 5: Generate report
    print("[5/5] Generating report...")
    report = ReportGenerator().generate(
        paper=paper,
        format_results=format_results,
        query_results=query_results,
        thematic_results=thematic_results,
        semantic_results=semantic_results,
    )

    output_path = Path(args.output)
    output_path.write_text(report, encoding="utf-8")
    print(f"      Report saved to: {output_path.absolute()}")


if __name__ == "__main__":
    main()
