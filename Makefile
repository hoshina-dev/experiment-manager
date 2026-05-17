.PHONY: serve test lint format requirements

serve:
	uv run uvicorn main:app --reload --port 8000

test:
	uv run pytest tests/ -v

lint:
	uv run black --check . && uv run isort --check .

format:
	uv run black . && uv run isort .

requirements:
	uv export --no-hashes --format requirements-txt > requirements.txt
