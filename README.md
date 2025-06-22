# POC Backend - FastAPI with AWS CDK

This project deploys a FastAPI backend application using AWS CDK with Fargate, Application Load Balancer, and custom domain configuration.

## Architecture

- **FastAPI Application**: Python web framework with hello endpoint
- **AWS Fargate**: Serverless container platform for running the application
- **Application Load Balancer**: HTTPS load balancer with SSL termination
- **Route53**: DNS management with custom subdomain
- **ACM**: SSL certificate management
- **VPC**: Isolated network with public and private subnets

## Project Structure

```
cdk-demo/
├── src/                          # FastAPI application source code
│   ├── main.py                   # FastAPI application
│   └── requirements.txt          # Python dependencies
├── Dockerfiles/                  # Docker configuration
│   └── Dockerfile               # Container definition
├── cdk_demo/                     # CDK stack definitions
│   ├── __init__.py
│   ├── cdk_demo_stack.py        # Main CDK stack
│   └── config.py                # Configuration management
├── env.base.example              # Example base environment configuration
├── env.dev.example               # Example development environment configuration
├── env.base                      # Base environment configuration (create from env.base.example)
├── env.dev                       # Development environment configuration (create from env.dev.example)
├── app.py                        # CDK application entry point
├── Makefile                      # Build and deployment automation
├── requirements.txt              # CDK dependencies
└── README.md                     # This file
```

## Environment Configuration

The project uses a two-tier configuration system. **Never commit your actual environment files to git** - they contain sensitive information.

### Setup Environment Files

1. **Copy the example files:**
   ```bash
   cp env.base.example env.base
   cp env.dev.example env.dev
   ```

2. **Edit the files with your actual values** (see sections below)

### Base Configuration (`env.base`)
Common configurations for all stages:
- AWS Region
- Domain name
- SSL certificate ARN
- Application settings

### Stage Configuration (`env.dev`, `env.staging`, `env.prod`)
Stage-specific configurations:
- Stage name
- Subdomain
- Container count
- Scaling parameters

## How to Get Required Values

### 1. AWS Region
```bash
# Your preferred AWS region
AWS_REGION=us-east-1
```

### 2. Domain Name
```bash
# Your registered domain (must have Route53 hosted zone)
DOMAIN_NAME=your-domain.com
```

**To find your domain:**
- Check your domain registrar
- Ensure you have a Route53 hosted zone for this domain

### 3. SSL Certificate ARN
```bash
# Your ACM certificate ARN
CERTIFICATE_ARN=arn:aws:acm:us-east-1:123456789012:certificate/your-certificate-id
```

**To get your certificate ARN:**

**Option A: Use AWS Console (Recommended for one-time setup)**
1. Go to [AWS Certificate Manager Console](https://console.aws.amazon.com/acm/)
2. Click **"Request a certificate"**
3. Choose **"Request a public certificate"**
4. Enter domain name: `*.your-domain.com` (wildcard for all subdomains)
5. Choose **"DNS validation"** (recommended)
6. Click **"Request"**
7. **IMPORTANT**: Complete DNS validation by adding the CNAME record to your Route53 hosted zone
8. Wait for certificate to be **"Issued"** (green status)
9. Copy the **Certificate ARN** from the certificate details

**Option B: Use AWS CLI**
```bash
# List your certificates
aws acm list-certificates --region us-east-1

# Get certificate details
aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/your-certificate-id
```

**Option C: Create new certificate via CLI**
```bash
# Request a new certificate (WILDCARD for all subdomains)
aws acm request-certificate \
  --domain-name "*.your-domain.com" \
  --validation-method DNS \
  --region us-east-1

# Verify the certificate is issued
aws acm describe-certificate --certificate-arn arn:aws:acm:us-east-1:123456789012:certificate/your-certificate-id
```

**⚠️ Important Notes:**
- **Use wildcard certificate** (`*.your-domain.com`) to cover all subdomains
- **Certificate must be in the same region** as your deployment (us-east-1)
- **DNS validation is required** - add the CNAME record to your Route53 hosted zone
- **Certificate must be "Issued"** (green status) before deployment

### 4. AWS Account ID
```bash
# Get your AWS account ID
aws sts get-caller-identity --query Account --output text
```

### 5. Route53 Hosted Zone ID
```bash
# List your hosted zones
aws route53 list-hosted-zones

# Get hosted zone details
aws route53 get-hosted-zone --id YOUR_HOSTED_ZONE_ID
```

## Prerequisites

1. **AWS CLI**: Configured with appropriate credentials
2. **AWS CDK**: Installed globally (`npm install -g aws-cdk`)
3. **Python 3.11+**: For running the application
4. **Docker**: For building container images

## Installation

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install CDK dependencies:
   ```bash
   npm install -g aws-cdk
   ```

4. **Setup environment files** (see Environment Configuration section above)

## Configuration

### Environment Variables

Create environment files based on your requirements:

**Base Configuration (`env.base`)**:
```
AWS_REGION=us-east-1
DOMAIN_NAME=your-domain.com
CERTIFICATE_ARN=arn:aws:acm:us-east-1:123456789012:certificate/your-certificate-id
APP_NAME=poc-backend
APP_PORT=8000
APP_MEMORY=512
APP_CPU=256
```

**Development Configuration (`env.dev`)**:
```
STAGE=dev
STACK_NAME=poc-backend-dev
SUBDOMAIN=demo-dev
CONTAINER_COUNT=1
CONTAINER_IMAGE_TAG=dev
MIN_CAPACITY=1
MAX_CAPACITY=2
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

## Deployment

### Using the Makefile (Recommended)

The easiest way to deploy is using the provided Makefile:

```bash
# Deploy to development
make deploy-dev

# Deploy to staging
make deploy STAGE=staging

# Deploy to production
make deploy STAGE=prod

# Show differences before deployment
make diff STAGE=dev

# Destroy a stack
make destroy STAGE=dev

# Synthesize CloudFormation template
make synth STAGE=dev
```

### Using CDK Directly

```bash
# Deploy to development
cdk deploy --context stage=dev --context name=poc-backend

# Deploy to staging
cdk deploy --context stage=staging --context name=poc-backend

# Deploy to production
cdk deploy --context stage=prod --context name=poc-backend
```

### Available Makefile Commands

```bash
# Show all available commands
make help

# Deployment
make deploy [STAGE=dev]     # Deploy to specified stage (default: dev)
make destroy [STAGE=dev]    # Destroy specified stage
make diff [STAGE=dev]       # Show differences before deployment
make synth [STAGE=dev]      # Synthesize CloudFormation template
make bootstrap              # Bootstrap CDK (first time only)

# Local Development
make local-build            # Build Docker image locally (for testing)
make local-run              # Run with Docker Compose
make local-stop             # Stop Docker Compose
make test                   # Run tests

# Utilities
make install                # Install Python dependencies
make clean                  # Clean up generated files
make logs [STAGE=dev]       # View CloudWatch logs
make validate [STAGE=dev]   # Validate configuration

# Convenience targets
make deploy-dev             # Deploy to development
make deploy-staging         # Deploy to staging
make deploy-prod            # Deploy to production
make destroy-dev            # Destroy development
make destroy-staging        # Destroy staging
make destroy-prod           # Destroy production
```

## API Endpoints

Once deployed, the following endpoints will be available:

- **Root**: `https://demo-{stage}.your-domain.com/`
- **Hello**: `https://demo-{stage}.your-domain.com/hello`
- **Health**: `https://demo-{stage}.your-domain.com/health`

## Local Development

### Running the FastAPI Application Locally

```bash
cd src
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Building and Testing Docker Image

```bash
# Build the image
docker build -f Dockerfiles/Dockerfile -t poc-backend:latest .

# Run the container
docker run -p 8000:8000 poc-backend:latest
```

### Using Docker Compose

```bash
# Start local development
make local-run

# Stop local development
make local-stop
```

## Infrastructure Components

### VPC
- Public subnets for load balancer
- Private subnets for Fargate tasks
- NAT Gateway for outbound internet access

### ECS Fargate
- Serverless container platform
- Auto-scaling based on CPU/memory usage
- Health checks and logging

### Application Load Balancer
- HTTPS listener with SSL termination
- Health checks on `/health` endpoint
- Target group for Fargate service

### Route53
- Custom subdomain routing
- A and CNAME records for load balancer

## Monitoring and Logging

- **CloudWatch Logs**: Application logs are sent to CloudWatch
- **ECS Service**: Monitor service health and metrics
- **Load Balancer**: Monitor traffic and health check status

## Security

- **VPC**: Network isolation with private subnets
- **SSL/TLS**: HTTPS with ACM certificate
- **IAM Roles**: Least privilege access for ECS tasks
- **Security Groups**: Restricted port access

## Cost Optimization

- **Fargate Spot**: Use spot instances for non-production workloads
- **Auto Scaling**: Scale down during low usage periods
- **Log Retention**: Configure appropriate log retention periods

## Troubleshooting

### Common Issues

1. **Certificate Not Found**: Ensure the certificate ARN is correct and in the right region
2. **Domain Not Resolving**: Check Route53 hosted zone configuration
3. **Container Not Starting**: Check ECS task logs in CloudWatch
4. **Health Check Failing**: Verify the `/health` endpoint is working
5. **Platform Mismatch**: Ensure CDK builds for `linux/amd64` platform

### Useful Commands

```bash
# Check CDK bootstrap status
cdk doctor

# List deployed stacks
cdk list

# View stack outputs
aws cloudformation describe-stacks --stack-name poc-backend-dev

# Check ECS service status
aws ecs describe-services --cluster poc-backend-dev --services poc-backend-dev

# View CloudWatch logs
make logs
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test locally and with CDK diff
4. Submit a pull request

## License

This project is licensed under the MIT License.
