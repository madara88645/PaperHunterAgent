# Example configuration for PaperHunterAgent
# Copy this file to config.py and modify as needed

# User-defined keywords for paper filtering
USER_KEYWORDS = [
    "quantum error correction",
    "surface code",
    "logical qubit",
    "quantum computing",
    "decoherence",
    "entanglement",
    "quantum algorithm",
    "quantum machine learning",
    "variational quantum eigensolvers",
    "quantum approximate optimization",
    "quantum neural networks",
    "quantum cryptography",
    "quantum communication",
    "quantum sensing",
    "quantum metrology",
]

# Search configuration
SEARCH_CONFIG = {
    "max_papers": 10,
    "initial_days_back": 1,
    "expanded_days_back": 14,
    "semantic_scholar_days_back": 10,
    "min_papers_threshold": 3,
}

# arXiv categories to search
ARXIV_CATEGORIES = [
    "quant-ph",  # Quantum Physics
    "hep-th",  # High Energy Physics - Theory
    "cond-mat",  # Condensed Matter
    "cs.QC",  # Computer Science - Quantum Computing
]

# Filtering rules
FILTER_CONFIG = {
    "min_abstract_words": 150,  # Rough estimate for 6+ pages
    "languages": ["english"],
    "exclude_preprints": False,
}

# Output configuration
OUTPUT_CONFIG = {
    "log_file": "quantum_research.log",
    "log_level": "INFO",
    "json_indent": 2,
    "max_concept_map_nodes": 20,
    "max_concept_map_edges": 30,
}

# API configuration
API_CONFIG = {
    "arxiv_max_results_per_category": 50,
    "semantic_scholar_base_url": "https://api.semanticscholar.org/graph/v1",
    "pdf_download_timeout": 30,
    "request_delay": 1.0,  # Seconds between API requests
}
