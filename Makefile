.PHONY: help install dev test lint fmt migrate makemigration seed seed-wipe run clean \
        bench-install bench-data bench-subset bench-run bench-report benchmark

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := python3 -m uv pip install --python $(PY)

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install:  ## Create the venv (Python 3.12 via uv) and install runtime + dev deps
	python3 -m uv venv --python 3.12 $(VENV)
	$(PIP) -r requirements-dev.txt

test:  ## Run the test suite
	$(VENV)/bin/pytest -q

lint:  ## Ruff check (no fixes)
	$(VENV)/bin/ruff check .

fmt:  ## Ruff safe autofix + import sort
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

migrate:  ## Apply migrations to $$DATABASE_URL
	$(VENV)/bin/alembic upgrade head

makemigration:  ## Autogenerate a migration: make makemigration m="add x"
	$(VENV)/bin/alembic revision --autogenerate -m "$(m)"

seed:  ## Seed the 4 demo patients
	$(PY) -m scripts.seed_demo

seed-wipe:  ## Remove the demo patients
	$(PY) -m scripts.seed_demo --wipe

run:  ## Run the dev server on :8000
	$(VENV)/bin/uvicorn app.main:app --reload --port 8000

clean:
	rm -rf $(VENV) .pytest_cache .ruff_cache **/__pycache__

# ── benchmark ────────────────────────────────────────────────────────────
bench-install:  ## Install the benchmark-only deps (datasets, jiwer, faster-whisper, ...)
	$(PIP) -r requirements-benchmark.txt

bench-data:  ## Download AfriSwitchCare parquet (needs HF_TOKEN + gated access)
	$(PY) -m benchmark.download_data

bench-subset:  ## Freeze the stratified test subset -> benchmark/frozen_manifest.jsonl
	$(PY) -m benchmark.subset

bench-run:  ## Transcribe the frozen subset with every model we have keys for
	$(PY) -m benchmark.run

bench-report:  ## Build benchmark/report/REPORT.md + charts from results/
	$(PY) -m benchmark.report

benchmark: bench-subset bench-run bench-report  ## Full pipeline (assumes deps + data)
	@echo "benchmark/report/REPORT.md is ready"
