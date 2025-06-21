#!/usr/bin/env python3
import os
import sys
from aws_cdk import App, Environment
from cdk_demo.cdk_demo_stack import CdkDemoStack

def main():
    app = App()
    
    # Get stage from context or command line argument
    stage = app.node.try_get_context('stage') or 'dev'
    name = app.node.try_get_context('name') or 'poc-backend'
    
    # Validate stage
    valid_stages = ['dev', 'staging', 'prod']
    if stage not in valid_stages:
        print(f"Error: Invalid stage '{stage}'. Valid stages are: {', '.join(valid_stages)}")
        sys.exit(1)
    
    # Get AWS environment from context or use defaults
    env = Environment(
        account=app.node.try_get_context('account') or os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=app.node.try_get_context('region') or os.getenv('CDK_DEFAULT_REGION') or 'us-east-1'
    )
    
    # Create stack with stage-specific configuration
    stack_name = f"{name}-{stage}"
    
    CdkDemoStack(
        app, 
        stack_name,
        stage=stage,
        env=env,
        description=f"POC Backend Stack for {stage} environment"
    )
    
    # Add tags to the app
    app.node.add_metadata('stage', stage)
    app.node.add_metadata('name', name)
    
    app.synth()

if __name__ == "__main__":
    main()
