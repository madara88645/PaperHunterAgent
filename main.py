#!/usr/bin/env python3
"""
QuantumResearchChain - PaperHunterAgent System
Main application entry point for the quantum research paper analysis system.
"""

import argparse
import json
import logging
import sys

from src.concept_map_agent import ConceptMapAgent
from src.paper_hunter_agent import PaperHunterAgent
from src.summarizer_agent import SummarizerAgent


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("quantum_research.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main(user_keywords=None, max_papers=10):
    """Main application function."""
    setup_logging()
    logger = logging.getLogger(__name__)

    if not user_keywords:
        # Default keywords if none supplied via CLI
        user_keywords = [
            "quantum error correction",
            "surface code",
            "logical qubit",
            "quantum computing",
            "decoherence",
            "entanglement",
            "quantum algorithm",
            "quantum machine learning",
        ]

    try:
        # Initialize agents
        logger.info("Initializing QuantumResearchChain agents...")
        paper_hunter = PaperHunterAgent(user_keywords=user_keywords)
        summarizer = SummarizerAgent()
        concept_mapper = ConceptMapAgent()

        # Step 1: Hunt for papers
        logger.info("Hunting for quantum papers...")
        papers_json = paper_hunter.hunt_papers(max_papers=max_papers)
        papers = json.loads(papers_json)

        if not papers:
            logger.warning("No papers found matching criteria")
            return

        logger.info(f"Found {len(papers)} papers")
        print("=" * 80)
        print("PAPER HUNTER RESULTS")
        print("=" * 80)
        print(papers_json)

        # Step 2: Summarize first paper as example
        if papers:
            first_paper = papers[0]
            logger.info(f"Summarizing paper: {first_paper['title']}")

            summary = summarizer.create_summary(first_paper)

            print("\n" + "=" * 80)
            print("SUMMARIZER RESULTS")
            print("=" * 80)
            print(summary)

            # Step 3: Create concept map
            if "⚠️ Unable to parse PDF" not in summary:
                logger.info("Creating concept map...")
                concept_map = concept_mapper.create_concept_map(summary)

                print("\n" + "=" * 80)
                print("CONCEPT MAP RESULTS")
                print("=" * 80)
                print("```mermaid")
                print(concept_map)
                print("```")
            else:
                logger.warning("Skipping concept map due to PDF parsing error")

    except Exception as e:
        logger.error(f"Error in main application: {e}")
        raise


def demo_individual_agents():
    """Demonstrate each agent individually with sample data."""
    setup_logging()

    print("=" * 80)
    print("QUANTUM RESEARCH CHAIN - AGENT DEMONSTRATION")
    print("=" * 80)

    # Demo PaperHunterAgent
    print("\n1. PAPER HUNTER AGENT DEMO")
    print("-" * 40)

    keywords = ["quantum error correction", "surface code"]
    hunter = PaperHunterAgent(user_keywords=keywords)

    # This will actually search arXiv - might take a moment
    papers_json = hunter.hunt_papers(max_papers=3)
    print(papers_json)

    # Demo SummarizerAgent with sample data
    print("\n2. SUMMARIZER AGENT DEMO")
    print("-" * 40)

    sample_paper = {
        "title": "Quantum Error Correction with Surface Codes",
        "authors": ["Alice Quantum", "Bob Physicist"],
        "published": "2024-01-15",
        "url_pdf": "https://arxiv.org/pdf/2401.00001.pdf",  # This is a placeholder
        "abstract": "We present a comprehensive study of quantum error correction using surface codes. Our approach demonstrates improved error thresholds and practical implementation strategies for near-term quantum computers.",
    }

    summarizer = SummarizerAgent()
    summary = summarizer.create_summary(sample_paper)
    print(summary)

    # Demo ConceptMapAgent
    print("\n3. CONCEPT MAP AGENT DEMO")
    print("-" * 40)

    sample_summary = """# Quantum Error Correction with Surface Codes

| Field | Value |
|-------|-------|
| Authors | Alice Quantum, Bob Physicist |
| Published | 2024-01-15 |
| Primary Topic | Quantum Error Correction |
| Key Equations | Eq. 1: H = sum_i Z_i Z_{i+1}, Eq. 2: |0_L⟩ = ..., Eq. 3: S = ⟨ψ|E|ψ⟩ |

## TL;DR (≤ 120 words)
This work presents a comprehensive study of quantum error correction using surface codes. The research demonstrates improved error thresholds through novel syndrome measurement techniques and practical implementation strategies for near-term quantum computers. We show that surface codes can achieve error rates below the fault-tolerance threshold with current hardware limitations.

## Main Contributions
• Novel syndrome measurement protocol for surface codes
• Improved error threshold analysis for practical implementations
• Hardware-efficient decoder design for near-term devices
• Demonstration of logical qubit operations with high fidelity

## Critical Assessment
**Why it matters:** This work advances practical quantum error correction by providing implementable solutions for current quantum hardware. The research bridges the gap between theoretical fault-tolerance and practical quantum computing applications.

**Potential weaknesses:** The methodology may require validation across different qubit technologies and larger code distances.

## Glossary
| Term | Definition (≤ 12 words) |
|------|-------------------------|
| Surface Code | Topological quantum error correcting code on 2D lattice |
| Logical Qubit | Error-corrected qubit encoded in multiple physical qubits |
| Syndrome | Error pattern detected through stabilizer measurements |
"""

    mapper = ConceptMapAgent()
    concept_map = mapper.create_concept_map(sample_summary)
    print("```mermaid")
    print(concept_map)
    print("```")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="QuantumResearchChain – hunt, summarize, and map quantum papers."
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        metavar="KEYWORD",
        help="One or more keywords to filter papers (default: built-in quantum set)",
    )
    parser.add_argument(
        "--max-papers",
        type=int,
        default=10,
        metavar="N",
        help="Maximum number of papers to return (default: 10)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the offline demo with sample data instead of the live pipeline",
    )
    args = parser.parse_args()

    if args.demo:
        demo_individual_agents()
    else:
        main(user_keywords=args.keywords, max_papers=args.max_papers)
