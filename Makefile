check-lint:
	. venv/bin/activate && (isort --check .; black --check .; flake8 .; mypy --strict .)

lint:
	. venv/bin/activate && (isort .; black .; flake8 .; mypy --strict .)

test:
	. venv/bin/activate && pytest
