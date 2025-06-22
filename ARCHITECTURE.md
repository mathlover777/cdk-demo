# CDK Architecture

## Overview

This project uses a modular CDK architecture with separate stacks for different concerns, promoting loose coupling and scalability.

## Stack Structure

### 1. Networking Stack (`NetworkingStack`)
**Location**: `cdk_demo/stacks/networking/vpc_stack.py`

**Responsibilities**:
- VPC creation with public/private subnets
- NAT Gateway setup
- SSL Certificate management
- Security Groups (ALB and ECS)
- Network infrastructure exports

**Exports**:
- VPC ID
- Public/Private subnet IDs
- Certificate ARN
- Security Group IDs

### 2. Backend Stack (`BackendStack`)
**Location**: `cdk_demo/stacks/backend/backend_stack.py`

**Responsibilities**:
- ECS Cluster and Fargate service
- Application Load Balancer
- Auto-scaling configuration
- Route53 DNS records
- FastAPI service deployment

**Imports from Networking Stack**:
- VPC and subnets
- Certificate
- Security groups

### 3. Shared Utilities
**Location**: `cdk_demo/stacks/shared/roles.py`

**Responsibilities**:
- IAM role creation utilities
- Reusable functions across stacks

## Key Benefits

### 1. **Loose Coupling**
- Each stack has a single responsibility
- Stacks communicate through well-defined interfaces (exports/imports)
- Changes in one stack don't affect others

### 2. **Scalability**
- Easy to add new services by creating new stacks
- Shared networking infrastructure reduces costs
- Independent deployment of services

### 3. **Maintainability**
- Clear separation of concerns
- Reusable utilities reduce code duplication
- Each service manages its own IAM roles

### 4. **Security**
- Per-stack IAM roles (principle of least privilege)
- Network isolation through VPC
- Service-specific security groups

## Deployment Order

1. **Networking Stack** - Creates VPC, certificate, security groups
2. **Backend Stack** - Deploys FastAPI service (depends on networking)

CDK automatically handles dependencies and deployment order.

## Future Extensions

### Adding New Services
1. Create new stack in `cdk_demo/stacks/`
2. Import VPC and certificate from networking stack
3. Create service-specific IAM roles using shared utilities
4. Add to `app.py` with appropriate dependencies

### Example: Auth Service
```python
# In app.py
auth_stack = AuthStack(app, f"poc-backend-auth-{stage}", stage=stage, env=env)
auth_stack.add_dependency(networking_stack)
```

## Configuration

Each stack uses the `Config` utility to load stage-specific configuration from:
- `env.base` - Base configuration
- `env.{stage}` - Stage-specific overrides

## Cross-Stack References

Uses CDK's `Fn.import_value()` to import resources from other stacks:
```python
vpc = ec2.Vpc.from_lookup(
    self, "ImportedVPC",
    vpc_id=Fn.import_value(f"poc-backend-{stage}-vpc-id")
)
``` 