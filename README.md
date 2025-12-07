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
├── cli/                    # Command-line interface
├── controllers/            # Kubernetes controllers (optional)
├── infrastructure/          # Pulumi infrastructure code
│   ├── __main__.py        # GKE cluster setup
│   ├── k8s_components.py  # K8s components (ArgoCD, Prometheus, etc.)
│   └── config.py          # Configuration helpers
├── templates/              # Application templates
│   ├── service/           # Service templates
│   ├── job/               # Job templates
│   └── worker/            # Worker templates
├── docs/                   # Documentation
│   ├── automatic-hpa.md          # Automatic HPA generation guide
│   ├── gke-infrastructure.md     # GKE cluster setup
│   ├── k8s-components.md          # Kubernetes components
│   ├── k8s-components-testing.md  # Component testing guide
│   ├── pre-commit-hooks.md        # Pre-commit hooks setup
│   └── security-gitignore.md      # Security and gitignore guide
└── tests/                  # Test suite
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
# Install Python dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### 3. Set Up Pre-commit Hooks

```bash
./setup-hooks.sh
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

### CLI Usage

```bash
# Deploy a service
mini-idp deploy service my-app \
  --image gcr.io/my-project/my-app:latest \
  --port 8080 \
  --replicas 3

# Deploy a job
mini-idp deploy job data-processor \
  --image gcr.io/my-project/processor:latest \
  --schedule "0 0 * * *"

# Deploy a worker
mini-idp deploy worker queue-worker \
  --image gcr.io/my-project/worker:latest \
  --replicas 5
```

### Web UI Usage

Start the FastAPI server:

```bash
cd api
uvicorn main:app --reload
```

Access the UI at `http://localhost:8000`

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

- [Web Service](docs/web-service.md) - FastAPI web service for deployments
- [API Reference](docs/api-reference.md) - Complete REST API documentation
- [Automatic HPA Generation](docs/automatic-hpa.md) - How automatic HPA defaults work
- [Fluent Bit Integration](docs/fluent-bit-integration.md) - Automatic log collection
- [Prometheus Metrics Integration](docs/prometheus-metrics.md) - Automatic metrics collection
- [External Secrets Integration](docs/external-secrets-integration.md) - Automatic secret injection
- [ArgoCD GitOps Integration](docs/argocd-gitops.md) - GitOps workflows with ArgoCD
- [GKE Infrastructure Setup](docs/gke-infrastructure.md) - Setting up GKE clusters
- [Kubernetes Components Guide](docs/k8s-components.md) - ArgoCD, Prometheus, etc.
- [Testing Guide](docs/k8s-components-testing.md) - Testing Kubernetes components
- [Security and GitIgnore](docs/security-gitignore.md) - Security best practices

## Roadmap

- [ ] Web UI for application deployment
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

