# Mini-IDP (Internal Developer Platform)

## 🚨 Problem
Developers often spend excessive time writing Kubernetes YAML, configuring infrastructure, and managing deployments—slowing down development and increasing operational complexity.

## ✅ Solution
Mini-IDP is a self-service Internal Developer Platform that enables developers to deploy applications to Kubernetes with zero YAML, using standardized templates and built-in best practices.

## 📈 Key Highlights
- One-command application deployment (CLI + API)  
- No YAML required for Kubernetes deployments  
- Built-in autoscaling, logging, metrics, and secret management  
- GitOps-enabled deployments using ArgoCD  
- Infrastructure managed via Pulumi (Infrastructure as Code)  

## 🏗 Architecture


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
## 🎯 Why This Matters
This project simulates how real platform engineering teams operate:
- Abstracting infrastructure complexity for developers  
- Standardizing deployment patterns across teams  
- Embedding observability, security, and scaling by default  
- Enabling self-service infrastructure and faster developer workflows

## 🧠 Design Thinking
This platform is designed around key platform engineering principles:
- Golden paths: opinionated templates for common workloads  
- Self-service: developers deploy without needing infra expertise  
- Built-in reliability: autoscaling, monitoring, and logging by default  
- GitOps-first: deployments are version-controlled and auditable

  
## Prerequisites

- Python 3.12+
- Pulumi CLI
- gcloud CLI
- kubectl
- A GCP project with billing enabled

## ⚙️ Example Usage

```bash
# Deploy a service
mini-idp deploy service my-app --image my-app:latest --port 8080

# Deploy with autoscaling and metrics
mini-idp deploy service my-api --autoscaling --metrics

```


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

## Documentation

### Getting Started
- [Getting Started Guide](docs/getting-started.md) - Complete guide to getting started with Mini-IDP


## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Inspired by the need for simplified Kubernetes deployments without the YAML complexity, this project aims to make Day 1 infrastructure setup as smooth as possible.

## Support

For issues, questions, or contributions, please open an issue on GitHub.



