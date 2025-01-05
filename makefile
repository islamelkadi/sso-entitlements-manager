# Define Colors
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m  # No Color

# Define variables
STACK_NAME = permia-sso-manager
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
	@poetry run pytest --cov=tests/unit/ --cov-report=xml:coverage.xml

# Formatting & Linting
.PHONY: format
format:
	@echo "Running python formatting"
	@poetry run black $(sources) --safe --line-length 250

	@echo "Running python linter"
	@poetry run pylint $(sources)

# Build lambda
.PHONY: build-backend
build-backend: env
	@echo "Creating requirements.txt file"
	@poetry export -f requirements.txt --output ./src/app/requirements.txt

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
	@poetry run pyclean . --debris --verbose

	@echo "Remove Poetry artifacts"
	@rm -rf .pytest_cache .coverage coverage.xml