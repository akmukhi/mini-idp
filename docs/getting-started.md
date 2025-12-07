# Getting Started with Mini-IDP

Complete guide to getting started with Mini-IDP for deploying applications to Kubernetes.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.12+** installed
- **kubectl** configured and connected to a Kubernetes cluster
- **GCP account** (for GKE, Secret Manager, Cloud Logging)
- **Pulumi CLI** (for infrastructure deployment)
- **gcloud CLI** (for GCP operations)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mini-idp.git
cd mini-idp
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### 3. Verify Installation

```bash
# Check CLI is available
mini-idp --version

# Check help
mini-idp --help
```

## Quick Start

### Option 1: Use Existing Kubernetes Cluster

If you already have a Kubernetes cluster:

```bash
# Configure kubectl
kubectl config use-context your-cluster-context

# Deploy your first application
mini-idp deploy service hello-world \
  --image nginx:latest \
  --port 80 \
  --replicas 2
```

### Option 2: Set Up GKE Cluster

If you need to set up a new GKE cluster:

1. **Configure GCP:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Deploy Infrastructure:**
   ```bash
   cd infrastructure
   
   # Set Pulumi configuration
   pulumi config set gcp:project YOUR_PROJECT_ID
   pulumi config set gcp:region us-central1
   pulumi config set cluster:name my-cluster
   
   # Deploy GKE cluster
   pulumi up
   ```

3. **Get Cluster Credentials:**
   ```bash
   gcloud container clusters get-credentials $(pulumi stack output cluster_name) \
     --region $(pulumi stack output cluster_location) \
     --project $(pulumi config get gcp:project)
   ```

4. **Deploy Kubernetes Components:**
   ```bash
   # Deploy ArgoCD, Prometheus, Fluent Bit, etc.
   # See infrastructure/README.md for details
   ```

See [GKE Infrastructure Setup](gke-infrastructure.md) for detailed instructions.

## Your First Deployment

### Deploy a Simple Service

```bash
mini-idp deploy service my-app \
  --image nginx:latest \
  --port 80 \
  --replicas 2
```

This creates:
- A Deployment with 2 replicas
- A Service exposing port 80
- Automatic HPA (if autoscaling enabled)
- Prometheus ServiceMonitor (if metrics enabled)
- Fluent Bit log collection (if logging enabled)

### Check Deployment Status

```bash
# List all applications
mini-idp list

# Check specific application status
mini-idp status my-app

# Watch status in real-time
mini-idp status my-app --watch
```

### Deploy with Full Features

```bash
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --replicas 3 \
  --namespace production \
  --env DATABASE_URL=postgres://... \
  --env API_KEY=secret123 \
  --external-secret db-password \
  --autoscaling \
  --min-replicas 2 \
  --max-replicas 10 \
  --cpu-target 70 \
  --metrics \
  --metrics-path /metrics \
  --logging \
  --logging-environment production
```

## Using the Web Service

### Start the API Server

```bash
# Development mode
python api/run.py

# Or with uvicorn
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Access the API

- **API Base**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Deploy via API

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

See [Web Service Documentation](web-service.md) for complete API usage.

## Next Steps

### Learn About Features

- [Automatic HPA Generation](automatic-hpa.md) - How autoscaling works
- [Fluent Bit Integration](fluent-bit-integration.md) - Log collection
- [Prometheus Metrics](prometheus-metrics.md) - Metrics collection
- [External Secrets](external-secrets-integration.md) - Secret management
- [ArgoCD GitOps](argocd-gitops.md) - GitOps workflows

### Explore Templates

```bash
# List available templates
mini-idp list templates  # Via API

# View template content
cat templates/service.yaml.j2

# Create custom template
# See templates/README.md
```

### Manage Applications

```bash
# List all applications
mini-idp list

# Check status
mini-idp status my-app

# Delete application
mini-idp delete my-app
```

## Common Workflows

### Development Workflow

```bash
# 1. Deploy to development namespace
mini-idp deploy service my-api \
  --image gcr.io/project/api:dev \
  --port 8080 \
  --namespace dev

# 2. Check status
mini-idp status my-api --namespace dev

# 3. Update deployment
mini-idp deploy service my-api \
  --image gcr.io/project/api:dev-v2 \
  --port 8080 \
  --namespace dev

# 4. Clean up
mini-idp delete my-api --namespace dev
```

### Production Workflow with GitOps

```bash
# 1. Generate manifests
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --write-manifests ./manifests/my-api

# 2. Review and commit
git add manifests/my-api
git commit -m "Deploy my-api v1.0"
git push

# 3. Create ArgoCD Application
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api \
  --git-branch main
```

## Troubleshooting

### Common Issues

1. **"kubectl not configured"**
   ```bash
   # Configure kubectl
   kubectl config use-context your-cluster
   ```

2. **"Template not found"**
   ```bash
   # Check available templates
   ls templates/
   ```

3. **"Permission denied"**
   ```bash
   # Check Kubernetes permissions
   kubectl auth can-i create deployments --namespace default
   ```

### Getting Help

- Check [Documentation](../README.md#documentation)
- Review [API Reference](api-reference.md)
- Open an issue on GitHub

## See Also

- [Main README](../README.md) - Complete project overview
- [GKE Infrastructure Setup](gke-infrastructure.md) - Cluster setup
- [Kubernetes Components](k8s-components.md) - Component installation
- [Security Guide](security-gitignore.md) - Security best practices

