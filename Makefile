.PHONY: lint
lint:
	python -m black --config pyproject.toml src tests
	flake8 src tests
	bandit -b ".bandit_baseline" -r src
	pylint src tests

.PHONY: .bandit_baseline
.bandit_baseline:
	bandit -f json -o .bandit_baseline -r src