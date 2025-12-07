# Mini-IDP Web Service

FastAPI-based web service for deploying applications to Kubernetes and managing templates through a REST API.

## Overview

The Mini-IDP web service provides:

- **RESTful API** - Standard HTTP endpoints for all operations
- **Interactive Documentation** - Auto-generated Swagger UI and ReDoc
- **Template Management** - Create, read, update, and delete templates
- **Deployment Management** - Deploy, list, get, and delete applications
- **Full Feature Support** - All CLI features available via API

## Quick Start

### Installation

Dependencies are already included in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Running the Service

#### Development Mode

```bash
# Using the run script
python api/run.py

# Or directly with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Accessing the API

Once running, access:

- **API Base URL**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Deployments

#### POST /api/deployments

Deploy an application to Kubernetes.

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/deployments" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "service",
    "name": "my-api",
    "image": "gcr.io/project/api:v1.0",
    "port": 8080,
    "replicas": 3,
    "autoscaling": true,
    "metrics": true,
    "logging": true
  }'
```

**Example with Full Configuration:**
```json
{
  "type": "service",
  "name": "my-api",
  "image": "gcr.io/project/api:v1.0",
  "namespace": "production",
  "port": 8080,
  "replicas": 3,
  "env": [
    {"name": "DATABASE_URL", "value": "postgres://localhost/db"},
    {"name": "API_KEY", "secret": "my-secret", "key": "api-key"}
  ],
  "external_secrets": ["database-password", "api-key:API_KEY"],
  "autoscaling": true,
  "min_replicas": 2,
  "max_replicas": 10,
  "cpu_target": 70,
  "metrics": true,
  "metrics_path": "/metrics",
  "logging": true,
  "logging_environment": "production",
  "gitops": true,
  "git_repo": "https://github.com/org/repo",
  "git_path": "manifests/my-api",
  "git_branch": "main"
}
```

#### GET /api/deployments

List all deployments.

```bash
curl "http://localhost:8000/api/deployments?namespace=production"
```

#### GET /api/deployments/{name}

Get deployment details.

```bash
curl "http://localhost:8000/api/deployments/my-api?namespace=production"
```

#### DELETE /api/deployments/{name}

Delete a deployment.

```bash
curl -X DELETE "http://localhost:8000/api/deployments/my-api?namespace=production"
```

### Templates

#### GET /api/templates

List all templates.

```bash
curl "http://localhost:8000/api/templates"
```

#### GET /api/templates/{name}

Get template content.

```bash
curl "http://localhost:8000/api/templates/service"
```

#### POST /api/templates

Create a new template.

```bash
curl -X POST "http://localhost:8000/api/templates" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "custom-service",
    "content": "apiVersion: apps/v1\nkind: Deployment\n..."
  }'
```

#### PUT /api/templates/{name}

Update a template.

```bash
curl -X PUT "http://localhost:8000/api/templates/service" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "apiVersion: apps/v1\nkind: Deployment\n..."
  }'
```

#### DELETE /api/templates/{name}

Delete a template.

```bash
curl -X DELETE "http://localhost:8000/api/templates/custom-service"
```

#### POST /api/templates/{name}/render

Render a template with context.

```bash
curl -X POST "http://localhost:8000/api/templates/service/render" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-api",
    "namespace": "default",
    "image": "gcr.io/project/api:v1.0",
    "port": 8080,
    "replicas": 3
  }'
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Deploy a service
response = requests.post(
    f"{BASE_URL}/api/deployments",
    json={
        "type": "service",
        "name": "my-api",
        "image": "gcr.io/project/api:v1.0",
        "port": 8080,
        "replicas": 3,
        "autoscaling": True,
        "metrics": True,
    }
)
print(response.json())

# List deployments
response = requests.get(f"{BASE_URL}/api/deployments")
print(response.json())

# Get template
response = requests.get(f"{BASE_URL}/api/templates/service")
template = response.json()
print(template["content"])

# Render template
response = requests.post(
    f"{BASE_URL}/api/templates/service/render",
    json={
        "name": "my-api",
        "namespace": "default",
        "image": "gcr.io/project/api:v1.0",
        "port": 8080,
        "replicas": 3,
    }
)
resources = response.json()
print(f"Generated {resources['count']} resources")
```

## JavaScript/TypeScript Client Example

```javascript
const BASE_URL = 'http://localhost:8000';

// Deploy a service
const deployResponse = await fetch(`${BASE_URL}/api/deployments`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    type: 'service',
    name: 'my-api',
    image: 'gcr.io/project/api:v1.0',
    port: 8080,
    replicas: 3,
    autoscaling: true,
    metrics: true,
  }),
});

const deployment = await deployResponse.json();
console.log(deployment);

// List deployments
const listResponse = await fetch(`${BASE_URL}/api/deployments`);
const deployments = await listResponse.json();
console.log(deployments);
```

## Configuration

### Environment Variables

The API uses the same configuration as the CLI:

- `KUBECONFIG`: Path to kubeconfig file
- `MINI_IDP_CONFIG_DIR`: Configuration directory (default: `~/.mini-idp`)

### CORS Configuration

CORS is currently configured to allow all origins. For production, update `api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

## Authentication

Currently, the API does not require authentication. For production:

1. **Add Authentication Middleware:**
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   
   security = HTTPBearer()
   
   async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
       token = credentials.credentials
       # Verify token
       if not is_valid_token(token):
           raise HTTPException(status_code=401, detail="Invalid token")
       return token
   
   @router.post("/api/deployments", dependencies=[Depends(verify_token)])
   async def create_deployment(...):
       ...
   ```

2. **Use API Keys:**
   ```python
   from fastapi import Header
   
   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("API_KEY"):
           raise HTTPException(status_code=401, detail="Invalid API key")
   ```

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Successful GET/PUT request
- `201 Created`: Successful POST request
- `204 No Content`: Successful DELETE request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `500 Internal Server Error`: Server error

Error responses include details:

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

## Production Deployment

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
docker build -t mini-idp-api .
docker run -p 8000:8000 -v ~/.kube:/root/.kube mini-idp-api
```

### Kubernetes Deployment

Deploy the API to Kubernetes:

```bash
mini-idp deploy service mini-idp-api \
  --image mini-idp-api:latest \
  --port 8000 \
  --replicas 3 \
  --autoscaling
```

### Reverse Proxy

Use nginx or similar for production:

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Monitoring

### Health Checks

The `/health` endpoint can be used for health checks:

```bash
curl http://localhost:8000/health
```

### Metrics

Add Prometheus metrics:

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

## See Also

- [API Reference](api-reference.md) - Complete API documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [CLI Documentation](../README.md) - Command-line interface

