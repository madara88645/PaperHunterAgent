# Contributing to PaperHunterAgent

Thank you for your interest in improving PaperHunterAgent! This guide will help you set up your development environment and walk you through the contribution workflow.

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Running Tests](#running-tests)
3. [Code Style](#code-style)
4. [Pre-commit Hooks](#pre-commit-hooks)
5. [Running CI Locally](#running-ci-locally)
6. [Submitting a Pull Request](#submitting-a-pull-request)
7. [Project Structure](#project-structure)

---

## Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/PaperHunterAgent.git
cd PaperHunterAgent

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install the package in editable mode with all runtime dependencies
pip install -e .

# 4. Install development tools
pip install pytest ruff black isort pre-commit

# 5. Configure your environment
cp .env.example .env
# Edit .env and add your (free) Semantic Scholar API key
```

---

## Running Tests

The test suite lives in `tests/` and uses the standard `unittest` framework (run via `pytest`).

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run a specific test class
pytest tests/test_agents.py::TestPaperHunterAgent -v

# Run a specific test
pytest tests/test_agents.py::TestSummarizerAgent::test_generate_tldr_caps_output_to_120_words -v
```

All tests mock external network calls (arXiv, Semantic Scholar, PDF downloads) so they run fully offline and complete in under a second.

---

## Code Style

This project uses three formatting/linting tools, all configured in `pyproject.toml`:

| Tool | Purpose | Command |
|------|---------|---------|
| [Ruff](https://docs.astral.sh/ruff/) | Fast linter (replaces flake8 + pyflakes + more) | `ruff check .` |
| [Black](https://black.readthedocs.io/) | Opinionated code formatter | `black .` |
| [isort](https://pycqa.github.io/isort/) | Import sorter | `isort .` |

**Line length:** 88 characters (Black default).

To auto-fix all style issues in one command:

```bash
black . && isort . && ruff check --fix .
```

---

## Pre-commit Hooks

The repository ships with a `.pre-commit-config.yaml`. Install the hooks once to have them run automatically on every `git commit`:

```bash
pre-commit install
```

To run all hooks manually against all files:

```bash
pre-commit run --all-files
```

---

## Running CI Locally

The CI workflow (`.github/workflows/ci.yml`) runs: `ruff check`, `black --check`, `isort --check-only`, then `pytest`.

Replicate this locally:

```bash
ruff check .
black --check .
isort --check-only .
pytest
```

If all four commands exit with code 0, your changes should pass CI.

---

## Submitting a Pull Request

1. **Branch** off `main`:
   ```bash
   git checkout -b feature/my-improvement
   ```

2. **Make your changes** — keep commits focused and descriptive.

3. **Add or update tests** for any new behaviour (follow the patterns in `tests/test_agents.py`).

4. **Run the full check suite** (see above) and fix any failures.

5. **Push** your branch and open a Pull Request against `main`.

6. In the PR description, explain *what* changed and *why*.

### Good PR checklist

- [ ] Tests added/updated and all passing (`pytest`)
- [ ] Linters pass (`ruff check . && black --check . && isort --check-only .`)
- [ ] No hardcoded secrets or API keys
- [ ] Documentation updated if behaviour changes (README, docstrings, `docs/architecture.md`)

---

## Project Structure

```
PaperHunterAgent/
├── src/
│   ├── __init__.py
│   ├── paper_hunter_agent.py   # Fetches and filters papers
│   ├── summarizer_agent.py     # Extracts and summarises PDF content
│   ├── concept_map_agent.py    # Builds Mermaid concept graphs
│   └── cli.py                  # `paperhunter` CLI entrypoint
├── tests/
│   └── test_agents.py          # Unit + integration tests
├── docs/
│   ├── architecture.md         # Architecture diagram + design decisions
│   └── mvp_review_report.md
├── main.py                     # Legacy / alternative entrypoint
├── pyproject.toml              # Packaging, tool config
├── requirements.txt            # Runtime dependencies
├── Dockerfile
├── .env.example
├── .pre-commit-config.yaml
├── CITATION.cff
└── LICENSE
```

---

If you have any questions, please [open an issue](https://github.com/madara88645/PaperHunterAgent/issues). We're happy to help!
