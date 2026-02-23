"""Tests for the paperhunter CLI (src/cli.py)."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the repo root is on the path so `src.*` imports resolve.
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import (
    _parse_keywords,
    build_parser,
    cmd_full_run,
    cmd_hunt,
    cmd_summarize,
)

SAMPLE_PAPERS = [
    {
        "title": "Quantum Error Correction with Surface Codes",
        "authors": ["Alice Quantum", "Bob Physicist"],
        "arxiv_id": "2401.00001",
        "doi": None,
        "published": "2024-01-15",
        "url_pdf": "https://arxiv.org/pdf/2401.00001.pdf",
        "abstract": "We present a comprehensive study of quantum error correction using surface codes.",
        "relevance_score": 90,
    }
]

SAMPLE_SUMMARY = (
    "# Quantum Error Correction with Surface Codes\n\n"
    "| Field | Value |\n|-------|-------|\n"
    "| Authors | Alice Quantum, Bob Physicist |\n"
    "| Published | 2024-01-15 |\n"
    "| Primary Topic | Quantum Error Correction |\n\n"
    "## TL;DR (≤ 120 words)\nGreat paper about surface codes.\n\n"
    "## Main Contributions\n• Novel decoder\n\n"
    "## Critical Assessment\n**Why it matters:** Important.\n\n"
    "## Glossary\n| Term | Definition |\n|------|------------|\n| Qubit | A quantum bit |\n"
)


class TestParseKeywords(unittest.TestCase):
    def test_single_keyword(self):
        self.assertEqual(_parse_keywords("quantum"), ["quantum"])

    def test_multiple_keywords(self):
        result = _parse_keywords("quantum error correction, surface code")
        self.assertEqual(result, ["quantum error correction", "surface code"])

    def test_strips_whitespace(self):
        result = _parse_keywords("  quantum  ,  surface code  ")
        self.assertEqual(result, ["quantum", "surface code"])

    def test_empty_string_returns_empty(self):
        self.assertEqual(_parse_keywords(""), [])


class TestBuildParser(unittest.TestCase):
    def test_hunt_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(
            [
                "hunt",
                "--keywords",
                "quantum error correction, surface code",
                "--max-papers",
                "5",
            ]
        )
        self.assertEqual(args.command, "hunt")
        self.assertEqual(args.max_papers, 5)
        self.assertIn("quantum", args.keywords)

    def test_summarize_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["summarize", "--input-json", "papers.json"])
        self.assertEqual(args.command, "summarize")
        self.assertEqual(args.input_json, "papers.json")

    def test_full_run_subcommand_parsed(self):
        parser = build_parser()
        args = parser.parse_args(
            ["full-run", "--keywords", "surface code", "--output-dir", "/tmp/out"]
        )
        self.assertEqual(args.command, "full-run")
        self.assertEqual(args.output_dir, "/tmp/out")

    def test_hunt_requires_keywords(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["hunt"])

    def test_summarize_requires_input_json(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["summarize"])


class TestCmdHunt(unittest.TestCase):
    def _make_args(self, keywords="quantum", max_papers=2, output=None):
        args = MagicMock()
        args.keywords = keywords
        args.max_papers = max_papers
        args.output = output
        return args

    def test_returns_0_on_success(self):
        args = self._make_args()
        with patch("src.cli.PaperHunterAgent") as MockHunter:
            MockHunter.return_value.hunt_papers.return_value = json.dumps(SAMPLE_PAPERS)
            result = cmd_hunt(args)
        self.assertEqual(result, 0)

    def test_returns_1_when_no_keywords(self):
        args = self._make_args(keywords="")
        result = cmd_hunt(args)
        self.assertEqual(result, 1)

    def test_writes_to_output_file(self):
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name
        try:
            args = self._make_args(output=output_path)
            with patch("src.cli.PaperHunterAgent") as MockHunter:
                MockHunter.return_value.hunt_papers.return_value = json.dumps(
                    SAMPLE_PAPERS
                )
                cmd_hunt(args)
            content = Path(output_path).read_text()
            self.assertIn("Quantum Error Correction", content)
        finally:
            os.unlink(output_path)


class TestCmdSummarize(unittest.TestCase):
    def test_returns_1_on_missing_file(self):
        args = MagicMock()
        args.input_json = "/nonexistent/path/papers.json"
        args.output = None
        result = cmd_summarize(args)
        self.assertEqual(result, 1)

    def test_returns_0_on_valid_input(self):
        import os
        import tempfile

        # Write a temporary papers JSON file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(SAMPLE_PAPERS, f)
            input_path = f.name
        try:
            args = MagicMock()
            args.input_json = input_path
            args.output = None
            with patch("src.cli.SummarizerAgent") as MockSummarizer:
                MockSummarizer.return_value.create_summary.return_value = SAMPLE_SUMMARY
                result = cmd_summarize(args)
            self.assertEqual(result, 0)
        finally:
            os.unlink(input_path)


class TestCmdFullRun(unittest.TestCase):
    def test_full_run_creates_output_structure(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            args = MagicMock()
            args.keywords = "quantum error correction, surface code"
            args.max_papers = 2
            args.output_dir = tmp_dir

            with (
                patch("src.cli.PaperHunterAgent") as MockHunter,
                patch("src.cli.SummarizerAgent") as MockSummarizer,
                patch("src.cli.ConceptMapAgent") as MockMapper,
            ):
                MockHunter.return_value.hunt_papers.return_value = json.dumps(
                    SAMPLE_PAPERS
                )
                MockSummarizer.return_value.create_summary.return_value = SAMPLE_SUMMARY
                MockMapper.return_value.create_concept_map.return_value = (
                    "graph TD\n    a[A] -->|uses| b[B]"
                )

                result = cmd_full_run(args)

            self.assertEqual(result, 0)
            out = Path(tmp_dir)
            self.assertTrue((out / "papers.json").exists())
            self.assertTrue((out / "summaries").is_dir())
            self.assertTrue((out / "concept_maps").is_dir())

    def test_full_run_returns_0_when_no_papers(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            args = MagicMock()
            args.keywords = "quantum"
            args.max_papers = 5
            args.output_dir = tmp_dir

            with patch("src.cli.PaperHunterAgent") as MockHunter:
                MockHunter.return_value.hunt_papers.return_value = "[]"
                result = cmd_full_run(args)

            self.assertEqual(result, 0)

    def test_full_run_returns_1_when_no_keywords(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            args = MagicMock()
            args.keywords = ""
            args.max_papers = 5
            args.output_dir = tmp_dir
            result = cmd_full_run(args)
            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
