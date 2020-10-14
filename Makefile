.PHONY: lint test test.unit test.integration help

.DEFAULT: all

all: lint test

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=80 --statistics
	mypy ./src ./tests

test:
	pytest -s -vvv

test.unit:
	pytest -s -vvv tests/test_unit.py

test.integration:
	pytest -s -vvv tests/test_integration.py

help:
	@echo "make lint"
	@echo "  run pylint and mypy"
	@echo "make test"
	@echo "  run all tests"
	@echo "make test.unit"
	@echo "  run only unit tests"
	@echo "make test.integration"
	@echo "  run only integration tests"
