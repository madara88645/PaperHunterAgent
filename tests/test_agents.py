import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from concept_map_agent import ConceptMapAgent
from paper_hunter_agent import PaperHunterAgent
from summarizer_agent import SummarizerAgent


class TestPaperHunterAgent(unittest.TestCase):
    """Test cases for PaperHunterAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.keywords = ["quantum error correction", "surface code"]
        self.agent = PaperHunterAgent(user_keywords=self.keywords)

    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.user_keywords, self.keywords)
        self.assertEqual(len(self.agent.arxiv_categories), 4)
        self.assertIn("quant-ph", self.agent.arxiv_categories)

    def test_matches_keywords_text(self):
        """Test keyword matching functionality."""
        text1 = "This paper discusses quantum error correction methods"
        text2 = "This is about classical computing algorithms"

        self.assertTrue(self.agent._matches_keywords_text(text1))
        self.assertFalse(self.agent._matches_keywords_text(text2))

    def test_calculate_relevance_score(self):
        """Test relevance score calculation."""
        # Mock paper object
        mock_paper = Mock()
        mock_paper.title = "Quantum Error Correction with Surface Codes"
        mock_paper.published = Mock()
        mock_paper.published.replace.return_value = Mock()

        # Mock datetime
        with patch("paper_hunter_agent.datetime") as mock_datetime:
            # Create a mock timedelta with days attribute
            mock_timedelta = Mock()
            mock_timedelta.days = 1
            mock_datetime.now.return_value.__sub__.return_value = mock_timedelta

            score = self.agent._calculate_relevance_score(mock_paper)
            self.assertGreaterEqual(score, 50)
            self.assertLessEqual(score, 100)


class TestSummarizerAgent(unittest.TestCase):
    """Test cases for SummarizerAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = SummarizerAgent()

    def test_initialization(self):
        """Test agent initialization."""
        self.assertIsNotNone(self.agent.logger)

    def test_extract_equations(self):
        """Test equation extraction."""
        text = "The Hamiltonian is $$H = \\sum_i Z_i Z_{i+1}$$ and the state is $$|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle$$"
        equations = self.agent.extract_equations(text)

        self.assertGreater(len(equations), 0)
        self.assertTrue(any("Eq." in eq for eq in equations))

    def test_identify_primary_topic(self):
        """Test primary topic identification."""
        title = "Quantum Error Correction using Surface Codes"
        abstract = "We demonstrate quantum error correction protocols using surface codes for fault-tolerant quantum computing."

        topic = self.agent.identify_primary_topic(title, abstract)
        self.assertEqual(topic, "Quantum Error Correction")

    def test_generate_tldr(self):
        """Test TL;DR generation."""
        abstract = (
            "This paper presents a novel approach to quantum error correction using surface codes. "
            * 20
        )
        full_text = "We conclude that our method shows significant improvements. " * 10

        tldr = self.agent.generate_tldr(abstract, full_text)
        word_count = len(tldr.split())
        self.assertLessEqual(word_count, 120)


class TestConceptMapAgent(unittest.TestCase):
    """Test cases for ConceptMapAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = ConceptMapAgent()

    def test_initialization(self):
        """Test agent initialization."""
        self.assertEqual(self.agent.max_nodes, 20)
        self.assertEqual(self.agent.max_edges, 30)

    def test_normalize_entity(self):
        """Test entity normalization."""
        entity = "the quantum error correction system"
        normalized = self.agent._normalize_entity(entity)
        self.assertEqual(normalized, "Quantum Error Correction System")

    def test_to_snake_case(self):
        """Test snake case conversion."""
        text = "Quantum Error Correction"
        snake_case = self.agent._to_snake_case(text)
        self.assertEqual(snake_case, "quantum_error_correction")

    def test_truncate_label(self):
        """Test label truncation."""
        long_label = "Very Long Quantum Error Correction System Protocol"
        truncated = self.agent._truncate_label(long_label)
        self.assertEqual(len(truncated.split()), 4)

    def test_extract_entities(self):
        """Test entity extraction from summary."""
        sample_summary = """# Quantum Error Correction with Surface Codes

| Primary Topic | Quantum Error Correction |

## TL;DR
This work demonstrates surface codes for quantum error correction with improved fidelity.

## Glossary
| Qubit | Quantum bit |
| Surface Code | Topological error correction code |
"""
        entities = self.agent.extract_entities(sample_summary)
        self.assertGreater(len(entities), 0)
        self.assertTrue(any("quantum" in str(e).lower() for e in entities))


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""

    def test_system_pipeline(self):
        """Test the complete system pipeline with mock data."""
        # Mock paper data
        mock_paper = {
            "title": "Test Quantum Paper",
            "authors": ["Test Author"],
            "published": "2024-01-01",
            "url_pdf": "https://example.com/test.pdf",
            "abstract": "This is a test abstract about quantum error correction and surface codes.",
        }

        # Test pipeline components
        summarizer = SummarizerAgent()
        mapper = ConceptMapAgent()

        # Mock PDF extraction to avoid network calls
        with patch.object(
            summarizer,
            "extract_pdf_text",
            return_value="Mock PDF content about quantum error correction",
        ):
            summary = summarizer.create_summary(mock_paper)
            self.assertIn("Test Quantum Paper", summary)

            # Test concept mapping
            concept_map = mapper.create_concept_map(summary)
            self.assertIn("graph TD", concept_map)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestPaperHunterAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestSummarizerAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestConceptMapAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
