.PHONY: venv install install-dev test run clean bundle dist dist-mac dist-win dist-linux

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
AUDISH := $(VENV)/bin/audish

venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel

install: venv
	$(PIP) install -e .

install-dev: venv
	$(PIP) install -e .
	$(PIP) install -r requirements-dev.txt

test: install-dev
	$(PYTEST) tests/ -v

run: install
	$(AUDISH) schedule \
		--app "Applicant Info.xlsx" \
		--fac "FA25 Faculty Avail.xlsx" \
		--map schools/juilliard/mapping.yaml \
		--rules schools/juilliard/rules.yaml \
		--out-schedule output/FinalSchedule.xlsx \
		--out-conflicts output/Conflicts.xlsx \
		--out-metrics output/Metrics.txt

# Bundle Python executable with PyInstaller
bundle: install-dev
	./scripts/build-python.sh

# Build complete distributable (Python + Electron)
dist: bundle
	./scripts/build-all.sh --mac

dist-mac: bundle
	./scripts/build-all.sh --mac

dist-win: bundle
	./scripts/build-all.sh --win

dist-linux: bundle
	./scripts/build-all.sh --linux

dist-all: bundle
	./scripts/build-all.sh --all

clean:
	rm -rf $(VENV)
	rm -rf .venv-build
	rm -rf *.egg-info
	rm -rf build dist
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -rf output/
	rm -rf electron/dist
	rm -rf electron/resources/audish-cli*
	find . -name "*.pyc" -delete





