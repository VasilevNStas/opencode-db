.PHONY: check test lint build clean install install-rich

check: lint test

test:
	python -m pytest tests/ -q

lint:
	python -m ruff check .

build: clean
	python -m build

clean:
	rm -rf dist/ build/ *.egg-info __pycache__ .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install:
	pip install -e .
	git config core.hooksPath .githooks

install-rich:
	pip install -e ".[rich]"
	git config core.hooksPath .githooks
