#!/bin/bash

# POC Backend Deployment Script
# Usage: ./deploy.sh [stage] [action]
# Example: ./deploy.sh dev deploy

set -e

# Default values
STAGE=${1:-dev}
ACTION=${2:-deploy}
STACK_NAME="poc-backend-${STAGE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate stage
valid_stages=("dev" "staging" "prod")
if [[ ! " ${valid_stages[@]} " =~ " ${STAGE} " ]]; then
    print_error "Invalid stage: $STAGE. Valid stages are: ${valid_stages[*]}"
    exit 1
fi

# Validate action
valid_actions=("deploy" "destroy" "diff" "synth")
if [[ ! " ${valid_actions[@]} " =~ " ${ACTION} " ]]; then
    print_error "Invalid action: $ACTION. Valid actions are: ${valid_actions[*]}"
    exit 1
fi

print_status "Deploying POC Backend for stage: $STAGE"
print_status "Stack name: $STACK_NAME"
print_status "Action: $ACTION"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    print_error "AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    print_error "AWS CDK is not installed. Please install it first."
    exit 1
fi

# Bootstrap CDK if needed
print_status "Checking CDK bootstrap..."
if ! cdk list > /dev/null 2>&1; then
    print_warning "CDK not bootstrapped. Bootstrapping now..."
    cdk bootstrap
fi

# Execute CDK command
case $ACTION in
    "deploy")
        print_status "Deploying stack..."
        cdk deploy --context stage=$STAGE --context name=poc-backend --require-approval never
        ;;
    "destroy")
        print_warning "Destroying stack..."
        cdk destroy --context stage=$STAGE --context name=poc-backend --force
        ;;
    "diff")
        print_status "Showing differences..."
        cdk diff --context stage=$STAGE --context name=poc-backend
        ;;
    "synth")
        print_status "Synthesizing CloudFormation template..."
        cdk synth --context stage=$STAGE --context name=poc-backend
        ;;
esac

print_status "Operation completed successfully!" 