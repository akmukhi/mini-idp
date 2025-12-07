# Mini-IDP

A CLI and REST API that deploys applications to Kubernetes with **no YAML required**. Deploy services, jobs, and workers using simple templates with built-in best practices for autoscaling, logging, metrics, secrets, and GitOps.

## Overview

Mini-IDP (Infrastructure Deployment Platform) eliminates the complexity of writing Kubernetes YAML manifests. Instead, you define your applications using simple templates, and the platform handles all the Kubernetes configuration automatically.

### Why This Project?

This project mirrors the work you would do on **Day 1** of building a production-ready platform:
- Standardized deployment patterns
- Built-in observability (logging, metrics)
- Security best practices (secret management)
- GitOps workflows
- Infrastructure as Code

## Features

### 🚀 **Zero YAML Deployment**
- Deploy applications without writing a single line of YAML
- Use simple, declarative templates for common patterns
- Automatic Kubernetes resource generation

### 📦 **Application Templates**
- **Services**: Stateless web applications and APIs
- **Jobs**: One-time and scheduled batch jobs
- **Workers**: Long-running background workers

### ⚙️ **Built-in Best Practices**

- **Autoscaling Defaults**: Automatic horizontal pod autoscaling configured out of the box
- **Logging Setup**: Integrated log aggregation with Fluent Bit forwarding to GCP Cloud Logging
- **Metrics**: Built-in Prometheus metrics with optional sidecar or library integration
- **Secret Injection**: Standardized secret management via External Secrets Operator with GCP Secret Manager
- **GitOps Deployment**: ArgoCD integration for automated, Git-based deployments

### 🛠️ **Infrastructure as Code**
- Pulumi-based infrastructure management
- Version-controlled infrastructure
- Reproducible deployments

## Tech Stack

- **Language**: Python 3.12+
- **Orchestration**: Kubernetes (GKE)
- **Cloud Provider**: Google Cloud Platform (GCP)
  - Cloud Run (optional)
- **Infrastructure as Code**: 
  - Pulumi (primary)
  - Terraform (alternative)
- **GitOps**: ArgoCD
- **API Layer**: FastAPI
- **Monitoring**: Prometheus + Grafana
- **Logging**: Fluent Bit → GCP Cloud Logging
- **Secrets**: External Secrets Operator + GCP Secret Manager
- **TLS**: cert-manager with Let's Encrypt

## Architecture

```
┌─────────────────┐
│   CLI / Web UI  │
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Template Engine │
│  (Python)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pulumi /        │
│  Terraform       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Kubernetes     │
│   (GKE)          │
│                  │
│  ┌───────────┐  │
│  │ ArgoCD    │  │
│  │ Prometheus│  │
│  │ Fluent Bit│  │
│  │ ESO       │  │
│  │ cert-mgr  │  │
│  └───────────┘  │
└─────────────────┘
```

## Project Structure

```
mini-idp/
├── api/                    # FastAPI web service
│   ├── main.py            # FastAPI application
│   ├── models.py          # Pydantic models
│   ├── run.py             # Development server
│   └── routers/           # API route handlers
│       ├── deployments.py # Deployment endpoints
│       └── templates.py   # Template management endpoints
├── cli/                    # Command-line interface
│   ├── main.py            # CLI entry point
│   ├── config.py          # Configuration management
│   └── commands/          # CLI commands
│       ├── deploy.py      # Deploy command
│       ├── list_apps.py   # List command
│       ├── status.py      # Status command
│       └── delete.py      # Delete command
├── lib/                    # Core library
│   ├── k8s_builder.py    # Kubernetes resource builders
│   ├── k8s_client.py      # Kubernetes client wrapper
│   ├── template_manager.py # Template management
│   ├── template_builder.py # Template-based builder
│   ├── deployment.py      # Deployment builder
│   ├── service.py         # Service builder
│   ├── job.py             # Job builder
│   ├── autoscaling.py     # HPA builder
│   ├── metrics.py         # ServiceMonitor builder
│   ├── secrets.py         # ExternalSecret builder
│   └── argocd.py          # ArgoCD Application builder
├── infrastructure/         # Pulumi infrastructure code
│   ├── __main__.py        # GKE cluster setup
│   ├── k8s_components.py  # K8s components (ArgoCD, Prometheus, etc.)
│   ├── k8s_config.py      # Component configuration
│   └── config.py          # Configuration helpers
├── templates/              # Application templates
│   ├── service.yaml.j2    # Service template
│   ├── job.yaml.j2        # Job template
│   └── worker.yaml.j2     # Worker template
├── docs/                   # Documentation
│   ├── getting-started.md  # Getting started guide
│   ├── web-service.md      # Web service documentation
│   ├── api-reference.md    # API reference
│   ├── automatic-hpa.md   # Automatic HPA guide
│   ├── fluent-bit-integration.md # Fluent Bit integration
│   ├── prometheus-metrics.md # Prometheus metrics
│   ├── external-secrets-integration.md # External Secrets
│   ├── argocd-gitops.md   # ArgoCD GitOps
│   ├── gke-infrastructure.md # GKE setup
│   ├── k8s-components.md  # Kubernetes components
│   ├── k8s-components-testing.md # Component testing
│   ├── security-gitignore.md # Security guide
│   └── pre-commit-hooks.md # Pre-commit hooks
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
└── README.md              # This file
```

## Prerequisites

- Python 3.12+
- Pulumi CLI
- gcloud CLI
- kubectl
- A GCP project with billing enabled

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/mini-idp.git
cd mini-idp
```

### 2. Install Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### 3. Verify Installation

```bash
# Check CLI is available
mini-idp --version

# Check help
mini-idp --help
```

### 4. Configure GCP

```bash
# Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 5. Deploy Infrastructure

```bash
cd infrastructure

# Set configuration
pulumi config set gcp:project YOUR_PROJECT_ID
pulumi config set gcp:region us-central1

# Deploy GKE cluster
pulumi up

# Deploy Kubernetes components
pulumi up --program k8s_components.py
```

See [GKE Infrastructure Guide](docs/gke-infrastructure.md) for detailed instructions.

### 6. Get Cluster Credentials

```bash
gcloud container clusters get-credentials $(pulumi stack output cluster_name) \
  --region $(pulumi stack output cluster_location) \
  --project $(pulumi config get gcp:project)
```

## Usage

### CLI Commands

#### Deploy Applications

```bash
# Deploy a service
mini-idp deploy service my-app \
  --image gcr.io/my-project/my-app:latest \
  --port 8080 \
  --replicas 3

# Deploy with autoscaling, metrics, and logging
mini-idp deploy service my-api \
  --image gcr.io/my-project/api:v1.0 \
  --port 8080 \
  --replicas 3 \
  --autoscaling \
  --min-replicas 2 \
  --max-replicas 10 \
  --cpu-target 70 \
  --metrics \
  --logging

# Deploy with external secrets
mini-idp deploy service my-api \
  --image gcr.io/my-project/api:v1.0 \
  --port 8080 \
  --external-secret database-password \
  --external-secret api-key:API_KEY

# Deploy with GitOps
mini-idp deploy service my-api \
  --image gcr.io/my-project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api

# Deploy a job
mini-idp deploy job data-processor \
  --image gcr.io/my-project/processor:latest

# Deploy a scheduled job (CronJob)
mini-idp deploy job daily-report \
  --image gcr.io/my-project/report:latest \
  --schedule "0 9 * * *"

# Deploy a worker
mini-idp deploy worker queue-worker \
  --image gcr.io/my-project/worker:latest \
  --replicas 5
```

#### List Applications

```bash
# List all applications
mini-idp list

# List applications in a namespace
mini-idp list --namespace production

# List only services
mini-idp list --type service

# Output as JSON
mini-idp list --output json

# Output as YAML
mini-idp list --output yaml
```

#### Check Application Status

```bash
# Show application status
mini-idp status my-api

# Show status in specific namespace
mini-idp status my-api --namespace production

# Watch status changes in real-time
mini-idp status my-api --watch
```

#### Delete Applications

```bash
# Delete an application (with confirmation)
mini-idp delete my-api

# Force delete without confirmation
mini-idp delete my-api --force

# Delete from specific namespace
mini-idp delete my-api --namespace production

# Delete specific type
mini-idp delete my-api --type service
```

### Web Service (REST API)

Start the FastAPI server:

```bash
# Development mode
python api/run.py

# Or with uvicorn directly
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API:
- **API Base**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

Example API call:

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
    "metrics": true
  }'
```

See [Web Service Documentation](docs/web-service.md) and [API Reference](docs/api-reference.md) for complete API documentation.

### Using Templates

Templates provide pre-configured patterns:

```bash
# Use a service template
mini-idp deploy --template service/python-fastapi \
  --name my-api \
  --image my-api:latest

# Use a job template
mini-idp deploy --template job/python-scheduled \
  --name daily-report \
  --schedule "0 9 * * *"
```

## Built-in Features

### Autoscaling

All deployments automatically include:
- **Automatic HPA Generation**: Intelligent min/max replica calculation based on deployment type
- **Type-Specific Defaults**: Services (70% CPU) and Workers (60% CPU) with optimized targets
- **Scaling Behavior**: Configured scale-up/down policies for stable operation
- **Resource Requests**: Automatic resource requests and limits

See [Automatic HPA Documentation](docs/automatic-hpa.md) for detailed information on how HPA defaults are calculated and how to customize them.

### Logging

- **Automatic Log Collection**: Fluent Bit automatically collects logs from all pods
- **GCP Cloud Logging**: Logs are forwarded to Google Cloud Logging
- **Structured Metadata**: Logs are tagged with app name, namespace, and environment
- **Zero Configuration**: Enabled by default with sensible defaults

See [Fluent Bit Integration Documentation](docs/fluent-bit-integration.md) for detailed information on log collection and viewing logs.

### Metrics

- **Automatic ServiceMonitor Generation**: Prometheus ServiceMonitor resources created automatically
- **Configurable Endpoints**: Customize metrics path, port, and scrape interval
- **Zero Configuration**: Works out of the box with `/metrics` endpoint
- **Prometheus Integration**: Automatic discovery and scraping by Prometheus

See [Prometheus Metrics Integration Documentation](docs/prometheus-metrics.md) for detailed information on metrics collection and configuration.

### Secrets

- **Automatic ExternalSecret Generation**: ExternalSecret resources created automatically
- **GCP Secret Manager Integration**: Sync secrets from Google Cloud Secret Manager
- **Automatic Secret Injection**: Secrets automatically injected into pods
- **Secure Authentication**: Uses Workload Identity for secure access
- **Automatic Refresh**: Secrets refreshed automatically at configured intervals

See [External Secrets Integration Documentation](docs/external-secrets-integration.md) for detailed information on secret management.

### GitOps

- **Automatic ArgoCD Application Generation**: ArgoCD Application resources created automatically
- **Git-Based Configuration**: All manifests stored in Git repositories
- **Automatic Synchronization**: ArgoCD automatically syncs changes from Git
- **Self-Healing**: ArgoCD automatically corrects drift from Git state
- **Flexible Workflows**: Support for both direct deployment and manifest generation

See [ArgoCD GitOps Integration Documentation](docs/argocd-gitops.md) for detailed information on GitOps workflows.
- Automatic sync from Git repositories
- Application health monitoring

## Configuration

### Environment Variables

```bash
export GCP_PROJECT=your-project-id
export GCP_REGION=us-central1
export KUBECONFIG=~/.kube/config
```

### Pulumi Configuration

```bash
# Set GCP project
pulumi config set gcp:project YOUR_PROJECT_ID

# Set region
pulumi config set gcp:region us-central1

# Configure cluster
pulumi config set cluster:name my-cluster
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.
```

### Code Quality

Pre-commit hooks automatically run:
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure tests pass and code is formatted
5. Submit a pull request

## Documentation

### Getting Started
- [Getting Started Guide](docs/getting-started.md) - Complete guide to getting started with Mini-IDP

### Features
- [Automatic HPA Generation](docs/automatic-hpa.md) - How automatic HPA defaults work
- [Fluent Bit Integration](docs/fluent-bit-integration.md) - Automatic log collection
- [Prometheus Metrics Integration](docs/prometheus-metrics.md) - Automatic metrics collection
- [External Secrets Integration](docs/external-secrets-integration.md) - Automatic secret injection
- [ArgoCD GitOps Integration](docs/argocd-gitops.md) - GitOps workflows with ArgoCD

### API & Web Service
- [Web Service](docs/web-service.md) - FastAPI web service for deployments
- [API Reference](docs/api-reference.md) - Complete REST API documentation

### Infrastructure
- [GKE Infrastructure Setup](docs/gke-infrastructure.md) - Setting up GKE clusters
- [Kubernetes Components Guide](docs/k8s-components.md) - ArgoCD, Prometheus, etc.
- [Testing Guide](docs/k8s-components-testing.md) - Testing Kubernetes components

### Development
- [Security and GitIgnore](docs/security-gitignore.md) - Security best practices
- [Pre-commit Hooks](docs/pre-commit-hooks.md) - Code quality setup

## Roadmap

- [x] CLI for application deployment
- [x] REST API for application deployment
- [x] Template management via API
- [x] List, status, and delete commands
- [ ] Web UI dashboard
- [ ] Additional template types
- [ ] Multi-cloud support (AWS, Azure)
- [ ] Custom resource definitions (CRDs)
- [ ] Application monitoring dashboard
- [ ] Cost optimization recommendations

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Inspired by the need for simplified Kubernetes deployments without the YAML complexity, this project aims to make Day 1 infrastructure setup as smooth as possible.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Built with ❤️ using Python, Kubernetes, and Pulumi**

