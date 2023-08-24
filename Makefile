lint:
	python -m black --config pyproject.toml . &&\
	flake8