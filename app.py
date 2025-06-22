#!/usr/bin/env python3
import os
import sys
from aws_cdk import App, Environment
from cdk_demo.stacks.networking.vpc_stack import NetworkingStack
from cdk_demo.stacks.backend.backend_stack import BackendStack

def main():
    app = App()
    
    # Get stage from context
    stage = app.node.try_get_context('stage') or 'dev'
    
    # Validate stage
    valid_stages = ['dev', 'staging', 'prod']
    if stage not in valid_stages:
        print(f"Error: Invalid stage '{stage}'. Valid stages are: {', '.join(valid_stages)}")
        sys.exit(1)
    
    # Get AWS environment
    env = Environment(
        account=os.getenv('CDK_DEFAULT_ACCOUNT'),
        region=os.getenv('CDK_DEFAULT_REGION') or 'us-east-1'
    )
    
    # Deploy Networking Stack first
    networking_stack = NetworkingStack(
        app, 
        f"poc-networking-{stage}",
        stage=stage,
        env=env,
        description=f"POC Backend Networking Stack for {stage} environment"
    )
    
    # Deploy Backend Stack (depends on networking stack)
    backend_stack = BackendStack(
        app, 
        f"poc-backend-{stage}",
        stage=stage,
        env=env,
        description=f"POC Backend Stack for {stage} environment"
    )
    
    # Add dependency: backend stack depends on networking stack
    backend_stack.add_dependency(networking_stack)
    
    # Add tags to the app
    app.node.add_metadata('stage', stage)
    
    app.synth()

if __name__ == "__main__":
    main()
