.PHONY: serve test lint format clean requirements observability-up observability-down observability-load observability-logs

serve:
	uv run uvicorn main:app --reload --port 8000

test:
	uv run pytest tests/ -v

lint:
	uv run black --check . && uv run isort --check .

format:
	uv run black . && uv run isort .

clean:
	rm -f experiments.db

requirements:
	uv export --no-hashes --format requirements-txt > requirements.txt

observability-up:
	docker compose -f docker-compose.observability.yml up -d --build

observability-down:
	docker compose -f docker-compose.observability.yml --profile loadtest down

observability-load:
	docker compose -f docker-compose.observability.yml --profile loadtest run --rm k6

observability-logs:
	docker compose -f docker-compose.observability.yml logs -f experiment-manager otel-collector
