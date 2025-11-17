.PHONY: venv install install-dev test run clean

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

clean:
	rm -rf $(VENV)
	rm -rf *.egg-info
	rm -rf build dist
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache
	rm -rf output/
	find . -name "*.pyc" -delete




