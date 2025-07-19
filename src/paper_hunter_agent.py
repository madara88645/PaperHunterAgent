import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

try:
    import arxiv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    arxiv = None

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    requests = None
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    def load_dotenv(*args, **kwargs):
        return False


class PaperHunterAgent:
    """
    PaperHunterAgent in the QuantumResearchChain.
    Goal: Find the most relevant and NEW quantum-science papers every day.
    """

    def __init__(self, user_keywords: List[str]):
        """Initialize the PaperHunterAgent."""

        load_dotenv()
        self.user_keywords = user_keywords
        self.arxiv_categories = ["quant-ph", "hep-th", "cond-mat", "cs.QC"]
        self.semantic_scholar_base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.logger = logging.getLogger(__name__)

    def search_arxiv_papers(self, days_back: int = 1) -> List[Dict[str, Any]]:
        """
        Search arXiv for papers in quantum categories from the last N days.

        Args:
            days_back: Number of days to look back

        Returns:
            List of paper dictionaries
        """
        if arxiv is None:
            self.logger.error("arxiv package not available")
            return []

        papers = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for category in self.arxiv_categories:
            try:
                # Build search query
                query = f"cat:{category}"

                # Search arXiv
                search = arxiv.Search(
                    query=query,
                    max_results=50,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending,
                )

                for paper in search.results():
                    # Check if paper is recent enough
                    if paper.published.replace(tzinfo=None) < cutoff_date:
                        continue

                    # Check if paper matches keywords
                    if not self._matches_keywords(paper):
                        continue

                    # Check page count (approximate from summary length)
                    if len(paper.summary.split()) < 150:  # Rough estimate for 6+ pages
                        continue

                    paper_data = {
                        "title": paper.title,
                        "authors": [str(author) for author in paper.authors],
                        "arxiv_id": paper.entry_id.split("/")[-1],
                        "doi": getattr(paper, "doi", None),
                        "published": paper.published.strftime("%Y-%m-%d"),
                        "url_pdf": paper.pdf_url,
                        "abstract": paper.summary,
                        "relevance_score": self._calculate_relevance_score(paper),
                    }
                    papers.append(paper_data)

            except Exception as e:
                self.logger.error(f"Error searching arXiv category {category}: {e}")

        return papers

    def search_semantic_scholar(
        self, arxiv_papers: List[Dict[str, Any]], days_back: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Query Semantic Scholar API for papers that cite or extend the arXiv hits.

        Args:
            arxiv_papers: List of arXiv papers to find citations for
            days_back: Number of days to look back for citations

        Returns:
            List of additional paper dictionaries
        """
        additional_papers = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for arxiv_paper in arxiv_papers:
            try:
                # Search for papers citing this arXiv paper
                arxiv_id = arxiv_paper["arxiv_id"]
                url = (
                    f"{self.semantic_scholar_base_url}/paper/arXiv:{arxiv_id}/citations"
                )

                headers = {}
                if self.api_key:
                    headers["x-api-key"] = self.api_key

                response = requests.get(
                    url,
                    params={"fields": "title,authors,year,url,abstract,citationCount"},
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    for citation in data.get("data", []):
                        paper = citation.get("citingPaper", {})

                        # Basic filtering
                        if not paper.get("title") or not paper.get("abstract"):
                            continue

                        # Check if recent enough (approximate)
                        if paper.get("year") and paper["year"] < cutoff_date.year:
                            continue

                        # Check if matches keywords
                        if not self._matches_keywords_text(
                            paper.get("title", "") + " " + paper.get("abstract", "")
                        ):
                            continue

                        paper_data = {
                            "title": paper["title"],
                            "authors": [
                                author.get("name", "Unknown")
                                for author in paper.get("authors", [])
                            ],
                            "arxiv_id": None,
                            "doi": paper.get("doi"),
                            "published": f"{paper.get('year', 'Unknown')}-01-01",  # Approximate
                            "url_pdf": paper.get("url"),
                            "abstract": paper.get("abstract", ""),
                            "relevance_score": min(
                                paper.get("citationCount", 0) * 5, 100
                            ),
                        }
                        additional_papers.append(paper_data)

            except Exception as e:
                self.logger.error(
                    f"Error searching Semantic Scholar for {arxiv_paper['arxiv_id']}: {e}"
                )

        return additional_papers

    def filter_and_deduplicate(
        self, papers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter and deduplicate papers according to rules.

        Args:
            papers: List of paper dictionaries

        Returns:
            Filtered and deduplicated papers
        """
        seen_ids = set()
        seen_dois = set()
        filtered_papers = []

        for paper in papers:
            # Check for duplicates
            arxiv_id = paper.get("arxiv_id")
            doi = paper.get("doi")

            if arxiv_id and arxiv_id in seen_ids:
                continue
            if doi and doi in seen_dois:
                continue

            # Add to seen sets
            if arxiv_id:
                seen_ids.add(arxiv_id)
            if doi:
                seen_dois.add(doi)

            filtered_papers.append(paper)

        # Sort by relevance score
        filtered_papers.sort(key=lambda x: x["relevance_score"], reverse=True)

        return filtered_papers

    def hunt_papers(self, max_papers: int = 10) -> str:
        """
        Main method to hunt for papers and return JSON output.

        Args:
            max_papers: Maximum number of papers to return

        Returns:
            JSON string with paper list
        """
        # Start with recent papers
        arxiv_papers = self.search_arxiv_papers(days_back=1)
        semantic_papers = self.search_semantic_scholar(arxiv_papers, days_back=10)

        all_papers = arxiv_papers + semantic_papers
        filtered_papers = self.filter_and_deduplicate(all_papers)

        # If fewer than 3 papers, expand search window
        if len(filtered_papers) < 3:
            self.logger.info("Expanding search window to ±7 days")
            arxiv_papers_extended = self.search_arxiv_papers(days_back=14)
            semantic_papers_extended = self.search_semantic_scholar(
                arxiv_papers_extended, days_back=17
            )

            all_papers = arxiv_papers_extended + semantic_papers_extended
            filtered_papers = self.filter_and_deduplicate(all_papers)

        # Limit to max_papers
        final_papers = filtered_papers[:max_papers]

        return json.dumps(final_papers, indent=2, ensure_ascii=False)

    def _matches_keywords(self, paper) -> bool:
        """Check if paper matches any user keywords."""
        text = f"{paper.title} {paper.summary}".lower()
        return self._matches_keywords_text(text)

    def _matches_keywords_text(self, text: str) -> bool:
        """Check if text matches any user keywords."""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in self.user_keywords)

    def _calculate_relevance_score(self, paper) -> int:
        """Calculate relevance score for a paper (0-100)."""
        score = 50  # Base score

        # Boost for keyword matches in title
        title_lower = paper.title.lower()
        for keyword in self.user_keywords:
            if keyword.lower() in title_lower:
                score += 20

        # Boost for recent publication
        try:
            days_old = (datetime.now() - paper.published.replace(tzinfo=None)).days
        except (AttributeError, TypeError):
            days_old = 0
        if days_old < 7:
            score += 20
        elif days_old < 30:
            score += 10

        return min(score, 100)
