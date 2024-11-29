# Define Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m  # No Color

# Define variables
STACK_NAME = permia-sso-manager

.ONESHELL:
sources = src tests

# Environment Setup
.PHONY: dev-env
dev-env:
	@echo "Creating Python virtual environment"
	@python3 -m venv .dev-venv

	@echo "Activating virtual environment"
	@. .venv/bin/activate

	@echo "Upgrading pip3"
	@pip3 install --upgrade pip

	@echo "Installing dependencies"
	@pip3 install .[dev]

	@echo "Creating requirements.txt file"
	@pip install . && pip freeze > ./src/app/requirements.txt

	@echo "Cleaning up requirements.txt file"
	@sed -i '' '/@ file:\/\//d' ./src/app/requirements.txt

	@echo "Install pre-commit hooks"
	@pre-commit install

.PHONY: env
env:
	@echo "Creating Python virtual environment"
	@python3 -m venv .venv

	@echo "Activating virtual environment"
	@. .venv/bin/activate

	@echo "Upgrading pip3"
	@pip3 install --upgrade pip

# Automated Testing
.PHONY: unittest
unittest:
	@echo "Generating coverage report"
	@pytest --cov=tests/unit/ --cov-report=xml:coverage.xml

# Formatting & Linting
.PHONY: format
format:
	@echo "Running python formatting"
	@black $(sources) --safe --line-length 250

	@echo "Running python linter"
	@pylint $(sources)

# Build lambda
.PHONY: build-backend
build-backend: env
	@echo "Creating requirements.txt file"
	@pip install . && pip freeze > ./src/app/requirements.txt

	@echo "Cleaning up requirements.txt file"
	@sed -i '' '/@ file:\/\//d' ./src/app/requirements.txt

	@echo "Building lambdas"
	@chmod +x ./tools/sam_build.sh
	@./tools/sam_build.sh -p ./src


# Clouformation Packaging
.PHONY: cfn-package
cfn-package:
	@echo "$(GREEN)Packging CloudFormation templates$(NC)\n"
	@mkdir ./cfn/templates/build | true
	@aws cloudformation package \
		--s3-bucket $$BUCKET \
		--template-file ./cfn/templates/main.yaml \
		--force-upload \
		--output-template-file ./cfn/templates/build/main.yaml > /dev/null;
	@echo "$(GREEN)Successfully packged CloudFormation templates$(NC)"

# Clouformation Deployments
.PHONY: cfn-deploy
cfn-deploy: cfn-package
	@echo "$(GREEN)Deploying CloudFormation templates$(NC)"
	@aws cloudformation deploy \
		--template-file ./cfn/templates/build/main.yaml \
		--stack-name $(STACK_NAME) \
		--s3-bucket $$BUCKET \
		--force-upload \
		--parameter-overrides file://cfn/params/main.json \
		--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM CAPABILITY_AUTO_EXPAND
	@echo "$(GREEN)Successfully deployed CloudFormation templates$(NC)\n"

# Remove cached python folders
.PHONY: cleanup
cleanup:
	@echo "Remove Python Debris"
	@pyclean . --debris --verbose

	@echo "Remove editable install artifacts"
	@rm -rf *.egg-info
