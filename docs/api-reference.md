# Mini-IDP API Reference

RESTful API for deploying applications to Kubernetes and managing templates.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. For production deployments, implement authentication middleware.

## Endpoints

### Health Check

#### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy"
}
```

### Deployments

#### POST /api/deployments

Deploy an application to Kubernetes.

**Request Body:**
```json
{
  "type": "service",
  "name": "my-api",
  "image": "gcr.io/project/api:v1.0",
  "namespace": "default",
  "port": 8080,
  "replicas": 1,
  "autoscaling": true,
  "metrics": true,
  "logging": true,
  "gitops": false
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Successfully deployed service 'my-api' to namespace 'default'",
  "resources": [...],
  "deployment_name": "my-api",
  "namespace": "default"
}
```

**Full Request Example:**
```json
{
  "type": "service",
  "name": "my-api",
  "image": "gcr.io/project/api:v1.0",
  "namespace": "production",
  "port": 8080,
  "replicas": 3,
  "env": [
    {"name": "DATABASE_URL", "value": "postgres://..."},
    {"name": "API_KEY", "secret": "my-secret", "key": "api-key"}
  ],
  "secrets": [
    {"secret": "my-secret", "key": "api-key"}
  ],
  "external_secrets": ["database-password", "api-key:API_KEY"],
  "autoscaling": true,
  "min_replicas": 2,
  "max_replicas": 10,
  "cpu_target": 70,
  "metrics": true,
  "metrics_path": "/metrics",
  "metrics_interval": "30s",
  "logging": true,
  "logging_environment": "production",
  "gitops": true,
  "git_repo": "https://github.com/org/repo",
  "git_path": "manifests/my-api",
  "git_branch": "main",
  "argocd_project": "production",
  "auto_sync": true,
  "prune": true,
  "self_heal": true,
  "dry_run": false
}
```

#### GET /api/deployments

List all deployments.

**Query Parameters:**
- `namespace` (optional): Filter by namespace

**Response:**
```json
[
  {
    "name": "my-api",
    "namespace": "default",
    "replicas": 3,
    "image": "gcr.io/project/api:v1.0",
    "ready_replicas": 3,
    "available_replicas": 3
  }
]
```

#### GET /api/deployments/{name}

Get deployment details.

**Path Parameters:**
- `name`: Deployment name

**Query Parameters:**
- `namespace` (default: "default"): Namespace

**Response:**
```json
{
  "name": "my-api",
  "namespace": "default",
  "replicas": 3,
  "image": "gcr.io/project/api:v1.0",
  "ready_replicas": 3,
  "available_replicas": 3,
  "labels": {...},
  "annotations": {...}
}
```

#### DELETE /api/deployments/{name}

Delete a deployment.

**Path Parameters:**
- `name`: Deployment name

**Query Parameters:**
- `namespace` (default: "default"): Namespace

**Response:** 204 No Content

### Templates

#### GET /api/templates

List all available templates.

**Response:**
```json
[
  {
    "name": "service",
    "path": "/path/to/templates/service.yaml.j2",
    "exists": true
  },
  {
    "name": "job",
    "path": "/path/to/templates/job.yaml.j2",
    "exists": true
  }
]
```

#### GET /api/templates/{name}

Get template content.

**Path Parameters:**
- `name`: Template name

**Response:**
```json
{
  "name": "service",
  "content": "...",
  "path": "/path/to/templates/service.yaml.j2"
}
```

#### POST /api/templates

Create a new template.

**Request Body:**
```json
{
  "name": "custom-service",
  "content": "apiVersion: apps/v1\nkind: Deployment\n..."
}
```

**Response (201 Created):**
```json
{
  "name": "custom-service",
  "content": "...",
  "path": "/path/to/templates/custom-service.yaml.j2"
}
```

#### PUT /api/templates/{name}

Update an existing template.

**Path Parameters:**
- `name`: Template name

**Request Body:**
```json
{
  "content": "apiVersion: apps/v1\nkind: Deployment\n..."
}
```

**Response:**
```json
{
  "name": "service",
  "content": "...",
  "path": "/path/to/templates/service.yaml.j2"
}
```

#### DELETE /api/templates/{name}

Delete a template.

**Path Parameters:**
- `name`: Template name

**Response:** 204 No Content

#### POST /api/templates/{name}/render

Render a template with context.

**Path Parameters:**
- `name`: Template name

**Request Body:**
```json
{
  "name": "my-api",
  "namespace": "default",
  "image": "gcr.io/project/api:v1.0",
  "port": 8080,
  "replicas": 3
}
```

**Response:**
```json
{
  "template": "service",
  "resources": [...],
  "count": 4
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

**Status Codes:**
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `500 Internal Server Error`: Server error

## Examples

### Deploy a Service

```bash
curl -X POST "http://localhost:8000/api/deployments" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "service",
    "name": "my-api",
    "image": "gcr.io/project/api:v1.0",
    "port": 8080,
    "replicas": 3,
    "autoscaling": true
  }'
```

### List Deployments

```bash
curl "http://localhost:8000/api/deployments?namespace=production"
```

### Get Template

```bash
curl "http://localhost:8000/api/templates/service"
```

### Render Template

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

## Interactive Documentation

The API includes interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## See Also

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes API Documentation](https://kubernetes.io/docs/reference/)

