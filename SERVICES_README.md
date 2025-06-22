# Services Structure

This project is organized with common code in `src` and service-specific code in dedicated directories.

## Directory Structure

```
src/
├── core/                   # Common configuration and utilities
│   ├── __init__.py
│   └── config.py          # Settings and configuration
├── models/                 # Common data models and schemas
│   └── __init__.py
├── utils/                  # Common utility functions
│   └── __init__.py
├── api/                    # FastAPI REST API service
│   ├── __init__.py
│   ├── main.py            # Main FastAPI application
│   └── api/               # API routes and middleware
│       ├── __init__.py
│       ├── routes/        # API route handlers
│       └── middleware/    # Custom middleware
└── main.py                # Main entry point (runs API by default)
```

## Requirements Organization

```
requirements/
├── api.txt                # API service dependencies
└── shared.txt             # Common dependencies across services
```

## Docker Organization

```
Dockerfiles/
└── api.Dockerfile         # API service container
```

## Running Services

### API Service
```bash
# Using Docker Compose
docker-compose up api

# Direct Python execution
cd src
python main.py
# or
python -m api.main
```

### Adding New Services

1. Create a new directory in `src/` for your service (e.g., `src/lambda-handler/`)
2. Add `__init__.py` and `main.py` files
3. Create a requirements file in `requirements/`
4. Create a Dockerfile in `Dockerfiles/`
5. Update `docker-compose.yml` to include the new service

### Example: Adding a Lambda Handler

```bash
# Create service structure
mkdir -p src/lambda-handler
touch src/lambda-handler/__init__.py
touch src/lambda-handler/main.py

# Create requirements
echo "boto3==1.34.0" > requirements/lambda.txt

# Create Dockerfile
cp Dockerfiles/api.Dockerfile Dockerfiles/lambda.Dockerfile
# Edit the Dockerfile for your lambda handler

# Update docker-compose.yml to include the new service
```

## Benefits of This Structure

1. **Common Code Reuse**: Core, models, and utils can be shared across services
2. **Clean Separation**: Service-specific code is isolated
3. **Easy to Scale**: Simple to add new services (API, Lambda, Fargate, etc.)
4. **Shared Dependencies**: Common dependencies managed in `shared.txt`
5. **Simple Organization**: Easy to understand and maintain 