PROJ := ofxstatement_fidelity
PYTHON := python3

# "all" should be the safe, verify-everything command
.PHONY: all
all: lint test

# --- Installation & Build ---

# Use editable install (-e) for development so changes take effect immediately
.PHONY: install
install:
	pip install -e .[dev]

# Build the distributable package (wheel/sdist) for PyPI
.PHONY: build
build:
	$(PYTHON) -m build

# --- Quality Assurance ---

.PHONY: test
test:
	pytest

# Run coverage report
.PHONY: coverage
coverage:
	pytest --cov=src/ofxstatement

# formatting (black) and static typing (mypy)
.PHONY: lint
lint: black mypy

.PHONY: black
black:
	black src tests

.PHONY: mypy
mypy:
	mypy src tests

# --- Maintenance ---

.PHONY: clean
clean:
	-rm -rf build
	-rm -rf dist
	-rm -rf src/$(PROJ).egg-info
	-rm -rf .pytest_cache
	-find . -type d -name "__pycache__" -exec rm -rf {} +


