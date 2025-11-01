# Makefile for Sendly Python SDK development

.PHONY: help install install-dev test test-unit test-integration lint format type-check security docs clean build publish

# Default target
help:
	@echo "Sendly Python SDK Development Commands"
	@echo "======================================"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install package in development mode"
	@echo "  install-dev      Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-cov         Run tests with coverage report"
	@echo "  test-all         Run tests across all Python versions (tox)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting (flake8)"
	@echo "  format           Auto-format code (black + isort)"
	@echo "  format-check     Check formatting without modifying files"
	@echo "  type-check       Run static type checking (mypy)"
	@echo "  security         Run security vulnerability scan"
	@echo "  quality          Run all quality checks"
	@echo ""
	@echo "Documentation:"
	@echo "  docs             Build documentation"
	@echo "  docs-live        Serve documentation with live reload"
	@echo ""
	@echo "Distribution:"
	@echo "  build            Build distribution packages"
	@echo "  publish-test     Publish to Test PyPI"
	@echo "  publish          Publish to PyPI"
	@echo ""
	@echo "Utilities:"
	@echo "  clean            Clean build artifacts and cache files"
	@echo "  examples         Run example scripts"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/

test-cov:
	pytest --cov=sendly --cov-report=html --cov-report=term-missing

test-all:
	tox

# Code quality
lint:
	flake8 sendly/ tests/ examples/

format:
	black sendly/ tests/ examples/
	isort sendly/ tests/ examples/

format-check:
	black --check --diff sendly/ tests/ examples/
	isort --check-only --diff sendly/ tests/ examples/

type-check:
	mypy sendly/

security:
	bandit -r sendly/
	safety check

quality: format-check lint type-check security
	@echo "All quality checks passed!"

# Documentation
docs:
	cd docs && make html

docs-live:
	sphinx-autobuild docs/ docs/_build/html --host 0.0.0.0 --port 8000

# Build and distribution
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

publish-test: build
	twine upload --repository testpypi dist/*

publish: build
	twine upload dist/*

# Examples
examples:
	@echo "Running example scripts..."
	@echo "Setting SENDLY_API_KEY=sl_test_example_key_for_testing"
	@SENDLY_API_KEY=sl_test_example_key_for_testing python -c "import examples.basic_usage; print('basic_usage.py compiled successfully')"
	@SENDLY_API_KEY=sl_test_example_key_for_testing python -c "import examples.advanced_usage; print('advanced_usage.py compiled successfully')"
	@echo "Example scripts validated!"

# Development workflow shortcuts
dev-setup: install-dev
	pre-commit install

quick-test: format-check lint test-unit
	@echo "Quick development tests passed!"

pre-commit: format lint type-check test-unit
	@echo "Pre-commit checks passed!"

# CI/CD helpers
ci-install:
	pip install -e ".[test]"

ci-test:
	pytest --cov=sendly --cov-report=xml --cov-report=term

# Version management
version:
	@python -c "import sendly; print(f'Current version: {sendly.__version__}')"

# Performance testing
benchmark:
	pytest tests/unit/test_http_client.py::TestHttpClient::test_exponential_backoff_sequence -v --tb=short

# Release checklist
release-check: clean quality test-all docs build
	@echo "Release checklist completed!"
	@echo "Ready to publish to PyPI"