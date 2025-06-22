# POC Backend Makefile
# Usage: make <target>

# Variables
STAGE ?= dev

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help install bootstrap deploy destroy diff synth local-build local-run test clean

# Default target
help:
	@echo "$(GREEN)POC Backend - Available Commands:$(NC)"
	@echo ""
	@echo "$(YELLOW)Deployment:$(NC)"
	@echo "  make deploy [STAGE=dev]     - Deploy to specified stage (default: dev)"
	@echo "  make destroy [STAGE=dev]    - Destroy specified stage"
	@echo "  make diff [STAGE=dev]       - Show differences before deployment"
	@echo "  make synth [STAGE=dev]      - Synthesize CloudFormation template"
	@echo "  make bootstrap              - Bootstrap CDK (first time only)"
	@echo ""
	@echo "$(YELLOW)Local Development:$(NC)"
	@echo "  make local-build            - Build Docker image locally (for testing)"
	@echo "  make local-run              - Run with Docker Compose"
	@echo "  make local-stop             - Stop Docker Compose"
	@echo "  make test                   - Run tests"
	@echo ""
	@echo "$(YELLOW)Utilities:$(NC)"
	@echo "  make install                - Install Python dependencies"
	@echo "  make clean                  - Clean up generated files"
	@echo "  make logs [STAGE=dev]       - View CloudWatch logs"

# Installation
install:
	@echo "$(GREEN)Installing Python dependencies...$(NC)"
	pip install -r requirements.txt

# CDK Bootstrap
bootstrap:
	@echo "$(GREEN)Bootstrapping CDK...$(NC)"
	cdk bootstrap

# Deployment commands
deploy:
	@echo "$(GREEN)Deploying to $(STAGE) environment...$(NC)"
	cdk deploy --context stage=$(STAGE) --require-approval never

destroy:
	@echo "$(YELLOW)Destroying $(STAGE) environment...$(NC)"
	cdk destroy --context stage=$(STAGE) --force

diff:
	@echo "$(GREEN)Showing differences for $(STAGE) environment...$(NC)"
	cdk diff --context stage=$(STAGE)

synth:
	@echo "$(GREEN)Synthesizing CloudFormation template for $(STAGE)...$(NC)"
	cdk synth --context stage=$(STAGE)

# Local development
local-build:
	@echo "$(GREEN)Building Docker image locally for testing...$(NC)"
	docker build -f Dockerfiles/Dockerfile -t poc-backend:latest .

local-run:
	@echo "$(GREEN)Starting local development environment...$(NC)"
	docker compose up

local-stop:
	@echo "$(YELLOW)Stopping local development environment...$(NC)"
	docker compose down

# Testing
test:
	@echo "$(GREEN)Running tests...$(NC)"
	cd src && python -m pytest test_main.py -v

# Utilities
clean:
	@echo "$(YELLOW)Cleaning up generated files...$(NC)"
	rm -rf cdk.out/
	rm -rf .pytest_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

logs:
	@echo "$(GREEN)Viewing CloudWatch logs for $(STAGE)...$(NC)"
	aws logs tail /aws/ecs/poc-backend --follow

# Convenience targets for different stages
deploy-dev:
	$(MAKE) deploy STAGE=dev

deploy-staging:
	$(MAKE) deploy STAGE=staging

deploy-prod:
	$(MAKE) deploy STAGE=prod

destroy-dev:
	$(MAKE) destroy STAGE=dev

destroy-staging:
	$(MAKE) destroy STAGE=staging

destroy-prod:
	$(MAKE) destroy STAGE=prod

# Validation
validate:
	@echo "$(GREEN)Validating configuration...$(NC)"
	@if [ ! -f "env.$(STAGE)" ]; then \
		echo "$(RED)Error: env.$(STAGE) file not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)Configuration validation passed$(NC)"

# Pre-deployment check
pre-deploy: validate
	@echo "$(GREEN)Pre-deployment checks passed$(NC)" 