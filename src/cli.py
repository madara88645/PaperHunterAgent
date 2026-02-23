#!/usr/bin/env python3
"""
paperhunter – CLI entrypoint for the PaperHunterAgent system.

Subcommands
-----------
hunt        Fetch papers from arXiv / Semantic Scholar and write JSON output.
summarize   Read a JSON papers file and summarize each paper as Markdown.
full-run    Hunt + summarize + concept-map in one shot.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

from src.concept_map_agent import ConceptMapAgent
from src.paper_hunter_agent import PaperHunterAgent
from src.summarizer_agent import SummarizerAgent


def _setup_logging(output_dir: str | None = None) -> None:
    """Configure logging to stdout and optionally to a file inside *output_dir*."""
    log_handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        log_handlers.append(
            logging.FileHandler(os.path.join(output_dir, "paperhunter.log"))
        )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=log_handlers,
    )


def _parse_keywords(raw: str) -> list[str]:
    """Split a comma-separated keyword string into a list."""
    return [kw.strip() for kw in raw.split(",") if kw.strip()]


# ---------------------------------------------------------------------------
# hunt
# ---------------------------------------------------------------------------


def cmd_hunt(args: argparse.Namespace) -> int:
    """Fetch papers and write JSON to *args.output*."""
    _setup_logging()
    logger = logging.getLogger(__name__)

    keywords = _parse_keywords(args.keywords)
    if not keywords:
        logger.error("No keywords provided. Use --keywords 'keyword1, keyword2'")
        return 1

    logger.info("Hunting papers with keywords: %s", keywords)
    hunter = PaperHunterAgent(user_keywords=keywords)
    papers_json = hunter.hunt_papers(max_papers=args.max_papers)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(papers_json, encoding="utf-8")
        logger.info("Results written to %s", args.output)
    else:
        print(papers_json)

    return 0


# ---------------------------------------------------------------------------
# summarize
# ---------------------------------------------------------------------------


def cmd_summarize(args: argparse.Namespace) -> int:
    """Read a JSON papers file and summarize every paper."""
    _setup_logging()
    logger = logging.getLogger(__name__)

    try:
        papers = json.loads(Path(args.input_json).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("Failed to read input JSON: %s", exc)
        return 1

    summarizer = SummarizerAgent()
    summaries: list[str] = []

    for paper in papers:
        logger.info("Summarizing: %s", paper.get("title", "<no title>"))
        summary = summarizer.create_summary(paper)
        summaries.append(summary)

    combined = "\n\n---\n\n".join(summaries)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(combined, encoding="utf-8")
        logger.info("Summaries written to %s", args.output)
    else:
        print(combined)

    return 0


# ---------------------------------------------------------------------------
# full-run
# ---------------------------------------------------------------------------


def cmd_full_run(args: argparse.Namespace) -> int:
    """Hunt papers, summarize them, and generate concept maps."""
    _setup_logging(output_dir=args.output_dir)
    logger = logging.getLogger(__name__)

    keywords = _parse_keywords(args.keywords)
    if not keywords:
        logger.error("No keywords provided. Use --keywords 'keyword1, keyword2'")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Hunt
    logger.info("Step 1/3 – Hunting papers with keywords: %s", keywords)
    hunter = PaperHunterAgent(user_keywords=keywords)
    papers_json = hunter.hunt_papers(max_papers=args.max_papers)
    papers = json.loads(papers_json)

    papers_path = output_dir / "papers.json"
    papers_path.write_text(papers_json, encoding="utf-8")
    logger.info("Found %d papers → %s", len(papers), papers_path)

    if not papers:
        logger.warning("No papers found. Exiting.")
        return 0

    # Step 2: Summarize
    logger.info("Step 2/3 – Summarizing %d papers", len(papers))
    summarizer = SummarizerAgent()
    mapper = ConceptMapAgent()

    summaries_dir = output_dir / "summaries"
    summaries_dir.mkdir(exist_ok=True)
    maps_dir = output_dir / "concept_maps"
    maps_dir.mkdir(exist_ok=True)

    for i, paper in enumerate(papers):
        title = paper.get("title", f"paper_{i}")
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        safe_title = safe_title[:60].strip()

        logger.info("  [%d/%d] %s", i + 1, len(papers), title)

        summary = summarizer.create_summary(paper)
        summary_path = summaries_dir / f"{safe_title}.md"
        summary_path.write_text(summary, encoding="utf-8")

        # Step 3: Concept map (skip on PDF error)
        if "⚠️ Unable to parse PDF" not in summary:
            concept_map = mapper.create_concept_map(summary)
            map_path = maps_dir / f"{safe_title}.mmd"
            map_path.write_text(concept_map, encoding="utf-8")

    logger.info("Full run complete. Results in: %s", output_dir)
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paperhunter",
        description="Hunt, summarize, and map quantum research papers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- hunt ----------------------------------------------------------------
    hunt_p = subparsers.add_parser(
        "hunt",
        help="Fetch papers from arXiv / Semantic Scholar and output JSON.",
    )
    hunt_p.add_argument(
        "--keywords",
        required=True,
        metavar='"kw1, kw2"',
        help="Comma-separated list of research keywords.",
    )
    hunt_p.add_argument(
        "--max-papers",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of papers to return (default: 10).",
    )
    hunt_p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write JSON output to FILE instead of stdout.",
    )

    # -- summarize -----------------------------------------------------------
    summarize_p = subparsers.add_parser(
        "summarize",
        help="Summarize papers from a JSON file produced by 'hunt'.",
    )
    summarize_p.add_argument(
        "--input-json",
        required=True,
        metavar="FILE",
        help="Path to the papers JSON file.",
    )
    summarize_p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write Markdown summaries to FILE instead of stdout.",
    )

    # -- full-run ------------------------------------------------------------
    fullrun_p = subparsers.add_parser(
        "full-run",
        help="Hunt + summarize + concept-map in one shot.",
    )
    fullrun_p.add_argument(
        "--keywords",
        required=True,
        metavar='"kw1, kw2"',
        help="Comma-separated list of research keywords.",
    )
    fullrun_p.add_argument(
        "--max-papers",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of papers to fetch (default: 10).",
    )
    fullrun_p.add_argument(
        "--output-dir",
        default="results",
        metavar="DIR",
        help="Directory to write all outputs (default: results/).",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "hunt": cmd_hunt,
        "summarize": cmd_summarize,
        "full-run": cmd_full_run,
    }
    handler = dispatch[args.command]
    sys.exit(handler(args))


if __name__ == "__main__":
    main()
