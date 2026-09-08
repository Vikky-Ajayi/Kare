.PHONY: help install dev test lint fmt migrate makemigration seed seed-wipe run clean

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
