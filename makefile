.ONESHELL:
sources = src tests


# Environment Setup
.PHONY: env
env:
	@echo "Creating Python virtual environment"
	@python3 -m venv .venv

	@echo "Activating virtual environment"
	@. .venv/bin/activate

	@echo "Upgrading pip3"
	@pip3 install --upgrade pip

	@echo "Installing dependencies"
	@pip3 install .[dev]

	@echo "Install pre-commit hooks"
	@pre-commit install

# Automated Testing
.PHONY: unittest
unittest:
	# @echo "Setting default region for testing"
	# @AWS_DEFAULT_REGION=us-east-1

	@echo "Generating coverage report"
	@pytest --cov=tests/ --cov-report=xml:coverage.xml

# Formatting & Linting
.PHONY: format
format:
	@echo "Running python formatting"
	@black $(sources) --safe --line-length 250

	@echo "Running python linter"
	@pylint $(sources)

# Remove cached python folders
.PHONY: cleanup
cleanup:
	@echo "Remove Python Debris"
	@pyclean . --debris --verbose

	@echo "Remove editable install artifacts"
	@rm -rf *.egg-info
