.PHONY: run serve clean

run:
	python main.py

serve:
	uv run uvicorn main:app --reload --port 8000

clean:
	rm -f data.db

requirements:
	uv export --no-hashes --format requirements-txt > requirements.txt