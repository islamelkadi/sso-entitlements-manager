# Define Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m  # No Color

# Define variables
LOCAL_DOCKER_IMAGE_NAME = sso-manager

.ONESHELL:
sources = src tests

.PHONY: dev-env
dev-env:
	@echo "Building Docker image"
	docker build -t $(LOCAL_DOCKER_IMAGE_NAME) .

	@echo "Starting the container"
	docker run -it \
		-v ${PWD}:/app \
		$(LOCAL_DOCKER_IMAGE_NAME)

# Automated Testing
.PHONY: unittest
unittest:
	@echo "Generating coverage report"
	@poetry run pytest --cov=tests/ --cov-report=xml:coverage.xml

# Formatting & Linting
.PHONY: format
format:
	@echo "Running python formatting"
	@poetry run black $(sources) --safe

	@echo "Running python linter"
	@poetry run pylint $(sources)

# Binary build system
.PHONY: build
build:
	@echo "$(GREEN)Building standalone executable$(NC)"
	@poetry run pyinstaller sso-manager.spec
	@echo "$(GREEN)Binary created in dist/ directory$(NC)"

.PHONY: clean-build
clean-build:
	@echo "Cleaning build artifacts"
	@rm -rf build/ dist/ *.spec __pycache__/

.PHONY: install-dev
install-dev:
	@echo "Installing development dependencies"
	@poetry install --with dev

# Remove cached python folders
.PHONY: cleanup
cleanup:
	@echo "Remove Python Debris"
	@poetry run pyclean . --debris --verbose

	@echo "Remove Poetry artifacts"
	@rm -rf .pytest_cache .coverage coverage.xml

.PHONY: clean-all
clean-all: cleanup clean-build
	@echo "All artifacts cleaned"