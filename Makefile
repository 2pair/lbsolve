lint:
	flake8 &&\
	python -m black --config pyproject.toml .