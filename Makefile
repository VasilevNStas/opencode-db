PYTHON ?= python

.PHONY: check check-python test lint schema-check build clean install install-rich

check: check-python lint test

check-python:
	@$(PYTHON) -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 12) else 1)' \
		|| (echo "ERROR: Python 3.12+ required (found $$($(PYTHON) --version 2>&1))."; echo "  Run: uv venv --python 3.13 && source .venv/bin/activate && make install"; exit 1)

test:
	$(PYTHON) -m pytest tests/ -q

lint:
	$(PYTHON) -m ruff check .

schema-check:
	$(PYTHON) scripts/check_schema_manifest.py

build: clean
	$(PYTHON) -m build

clean:
	rm -rf dist/ build/ *.egg-info __pycache__ .ruff_cache .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

install:
	pip install -e .
	git config core.hooksPath .githooks

install-rich:
	pip install -e ".[rich]"
	git config core.hooksPath .githooks
