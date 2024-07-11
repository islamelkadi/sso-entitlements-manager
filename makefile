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
	@pip3 install -r requirements.txt

# Automated Testing
.PHONY: unittest
unittest:
	@echo "Running unit tests"
	@pytest tests/unit

# Formatting & Linting
.PHONY: format
format:
	@echo "Running python formatting"
	@black $(sources)

	@echo "Running python linter"
	@pylint $(sources)

# Remove cached python folders
.PHONY: cleanup
cleanup:
	@echo "Remove Python Debris"
	@pyclean . --debris --verbose
	
	@echo "Remove editable install artifacts"
	@rm -rf *.egg-info
