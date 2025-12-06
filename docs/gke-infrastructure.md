# GKE Infrastructure Usage Guide

This guide provides detailed instructions for using the GKE (Google Kubernetes Engine) cluster infrastructure setup for the mini-idp project.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Testing](#testing)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)

## Overview

The GKE infrastructure setup provides a production-ready Kubernetes cluster with:

- **Autoscaling Node Pools**: Automatically scales nodes based on workload demand
- **Workload Identity**: Secure pod-to-GCP service authentication
- **Network Policies**: Pod-to-pod communication control
- **Monitoring/Logging**: Integrated Google Cloud Monitoring and Logging

All infrastructure is defined using Pulumi and can be managed through code.

## Quick Start

### Prerequisites

1. **Install Pulumi CLI:**
   ```bash
   curl -fsSL https://get.pulumi.com | sh
   ```

2. **Install gcloud CLI and authenticate:**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Set your GCP project:**
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

### Initial Setup

1. **Navigate to infrastructure directory:**
   ```bash
   cd infrastructure
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Pulumi stack (if not already done):**
   ```bash
   pulumi stack init dev  # or 'prod', 'staging', etc.
   ```

5. **Configure required settings:**
   ```bash
   pulumi config set gcp:project YOUR_PROJECT_ID
   pulumi config set gcp:region us-central1
   ```

6. **Preview the deployment:**
   ```bash
   pulumi preview
   ```

7. **Deploy the cluster:**
   ```bash
   pulumi up
   ```

## Configuration

### Required Configuration

**GCP Project ID** (required):
```bash
pulumi config set gcp:project YOUR_PROJECT_ID
```

### Optional Configuration

**GCP Region** (defaults to `us-central1`):
```bash
pulumi config set gcp:region us-west1
```

**Cluster Name** (defaults to `mini-idp-cluster`):
```bash
pulumi config set cluster:name my-custom-cluster-name
```

**Node Pool Configuration:**

```bash
# Machine type (default: e2-medium)
pulumi config set nodePool:machineType e2-standard-4

# Minimum nodes (default: 1)
pulumi config set nodePool:minNodes 2

# Maximum nodes (default: 3)
pulumi config set nodePool:maxNodes 5

# Disk size in GB (default: 20)
pulumi config set nodePool:diskSizeGb 50

# Disk type (default: pd-standard)
pulumi config set nodePool:diskType pd-ssd
```

### Viewing Configuration

**View all configuration:**
```bash
pulumi config
```

**View specific configuration value:**
```bash
pulumi config get gcp:project
pulumi config get gcp:region
```

**View configuration as JSON:**
```bash
pulumi config --json
```

### Configuration Files

Configuration is stored in Pulumi stack files (`.pulumi/stacks/`). These are automatically managed by Pulumi and should not be edited manually. Use `pulumi config set` commands instead.

## Deployment

### First-Time Deployment

1. **Ensure prerequisites are met** (see [Quick Start](#quick-start))

2. **Set required configuration:**
   ```bash
   pulumi config set gcp:project YOUR_PROJECT_ID
   ```

3. **Preview changes:**
   ```bash
   pulumi preview
   ```
   Review the output to see what resources will be created.

4. **Deploy:**
   ```bash
   pulumi up
   ```
   Type `yes` when prompted to confirm.

5. **Get cluster credentials:**
   ```bash
   gcloud container clusters get-credentials $(pulumi stack output cluster_name) \
     --region $(pulumi stack output cluster_location) \
     --project $(pulumi config get gcp:project)
   ```

6. **Verify cluster:**
   ```bash
   kubectl get nodes
   kubectl cluster-info
   ```

### Updating Configuration

To update the cluster configuration:

1. **Modify configuration:**
   ```bash
   pulumi config set nodePool:maxNodes 10
   ```

2. **Preview changes:**
   ```bash
   pulumi preview
   ```

3. **Apply changes:**
   ```bash
   pulumi up
   ```

### Multiple Environments

You can manage multiple environments using different Pulumi stacks:

```bash
# Create stacks for different environments
pulumi stack init dev
pulumi stack init staging
pulumi stack init prod

# Switch between stacks
pulumi stack select dev
pulumi config set gcp:project dev-project-id

pulumi stack select prod
pulumi config set gcp:project prod-project-id
```

## Testing

### Syntax Validation

**Test Python syntax:**
```bash
python3 -m py_compile __main__.py config.py
```

**Test imports:**
```bash
python3 -c "import pulumi; import pulumi_gcp; from config import *; print('Imports OK')"
```

### Configuration Testing

**Test configuration helper functions:**
```bash
# First set config via CLI
pulumi config set gcp:project test-project
pulumi config set gcp:region us-central1

# Then test in Python
python3 -c "
from config import *
print('GCP Project:', get_gcp_project())
print('Region:', get_gcp_region())
print('Cluster Name:', get_cluster_name())
print('Node Pool Config:', get_node_pool_config())
"
```

**Note:** Pulumi Config objects are read-only in Python. Use `pulumi config set` from the command line to set values.

### Dry-Run Testing

**Preview without deploying:**
```bash
pulumi preview
```

This shows what resources would be created without actually creating them.

### Post-Deployment Testing

**Verify cluster features:**

```bash
CLUSTER_NAME=$(pulumi stack output cluster_name)
REGION=$(pulumi stack output cluster_location)
PROJECT=$(pulumi config get gcp:project)

# Test Workload Identity
gcloud container clusters describe $CLUSTER_NAME \
  --region $REGION \
  --project $PROJECT \
  --format="value(workloadIdentityConfig.workloadPool)"

# Test Network Policies
gcloud container clusters describe $CLUSTER_NAME \
  --region $REGION \
  --project $PROJECT \
  --format="value(networkPolicy.enabled)"

# Test Monitoring
gcloud container clusters describe $CLUSTER_NAME \
  --region $REGION \
  --project $PROJECT \
  --format="value(monitoringService)"

# Test Logging
gcloud container clusters describe $CLUSTER_NAME \
  --region $REGION \
  --project $PROJECT \
  --format="value(loggingService)"
```

## Common Operations

### Accessing Cluster Information

**Get cluster outputs:**
```bash
# All outputs
pulumi stack output --json

# Specific outputs
pulumi stack output cluster_name
pulumi stack output cluster_endpoint
pulumi stack output cluster_workload_identity_pool
pulumi stack output node_pool_name
```

### Connecting to the Cluster

**Get kubectl credentials:**
```bash
gcloud container clusters get-credentials $(pulumi stack output cluster_name) \
  --region $(pulumi stack output cluster_location) \
  --project $(pulumi config get gcp:project)
```

**Verify connection:**
```bash
kubectl get nodes
kubectl get namespaces
```

### Scaling Nodes

**Update node pool configuration:**
```bash
# Update max nodes
pulumi config set nodePool:maxNodes 10

# Apply changes
pulumi up
```

**Manual scaling (temporary):**
```bash
gcloud container clusters resize $(pulumi stack output cluster_name) \
  --node-pool $(pulumi stack output node_pool_name) \
  --num-nodes 5 \
  --region $(pulumi stack output cluster_location)
```

### Viewing Logs

**Cluster logs:**
```bash
gcloud logging read "resource.type=k8s_cluster" \
  --project $(pulumi config get gcp:project) \
  --limit 50
```

**Node pool logs:**
```bash
gcloud logging read "resource.type=k8s_node" \
  --project $(pulumi config get gcp:project) \
  --limit 50
```

### Monitoring

**View cluster metrics in Cloud Console:**
- Navigate to [GKE Clusters](https://console.cloud.google.com/kubernetes/clusters)
- Select your cluster
- View metrics in the "Monitoring" tab

**Access via gcloud:**
```bash
gcloud monitoring dashboards list \
  --project $(pulumi config get gcp:project)
```

## Troubleshooting

### Authentication Issues

**Error: "Could not automatically determine credentials"**

```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Verify authentication
gcloud auth list
```

### API Not Enabled

**Error: "API not enabled"**

The Pulumi code automatically enables required APIs. If issues persist:

```bash
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

### Insufficient Permissions

**Error: "Permission denied"**

Ensure your GCP account has these roles:
- `roles/container.admin`
- `roles/compute.admin`
- `roles/iam.serviceAccountUser`
- `roles/serviceusage.serviceUsageAdmin`

```bash
# Check current permissions
gcloud projects get-iam-policy $(pulumi config get gcp:project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:YOUR_EMAIL"
```

### Configuration Errors

**Error: "Missing required configuration"**

```bash
# Check current configuration
pulumi config

# Set missing values
pulumi config set gcp:project YOUR_PROJECT_ID
```

**Error: "Config value not found"**

Use `pulumi config get` to check if a value exists, or set it with `pulumi config set`.

### Cluster Creation Failures

**Cluster stuck in "PROVISIONING" state:**

1. Check for quota limits:
   ```bash
   gcloud compute project-info describe \
     --project $(pulumi config get gcp:project)
   ```

2. Check for API issues:
   ```bash
   gcloud services list --enabled \
     --project $(pulumi config get gcp:project)
   ```

3. Review cluster status:
   ```bash
   gcloud container clusters describe $(pulumi stack output cluster_name) \
     --region $(pulumi stack output cluster_location) \
     --project $(pulumi config get gcp:project)
   ```

### Network Policy Issues

**Pods cannot communicate:**

Network policies are enabled by default. You may need to create NetworkPolicy resources to allow traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - {}
  egress:
  - {}
```

### Workload Identity Issues

**Pods cannot access GCP services:**

1. Verify Workload Identity is enabled:
   ```bash
   gcloud container clusters describe $(pulumi stack output cluster_name) \
     --region $(pulumi stack output cluster_location) \
     --format="value(workloadIdentityConfig.workloadPool)"
   ```

2. Configure service account binding (see [Workload Identity documentation](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity))

## Best Practices

1. **Use separate stacks for different environments** (dev, staging, prod)

2. **Set up billing alerts** in GCP Console to monitor costs

3. **Use smaller machine types for development** to reduce costs

4. **Regularly review and update node pool configurations** based on actual usage

5. **Enable auto-upgrade and auto-repair** (already enabled by default)

6. **Monitor cluster metrics** regularly to optimize resource usage

7. **Use Workload Identity** instead of service account keys for better security

8. **Review network policies** to ensure proper pod-to-pod communication

## Cost Optimization

- **Use appropriate machine types**: Start with smaller instances and scale up as needed
- **Set reasonable autoscaling limits**: Don't set max nodes too high
- **Use preemptible nodes** for non-production workloads (requires code modification)
- **Monitor and adjust**: Regularly review actual usage and adjust configurations
- **Clean up unused resources**: Destroy test clusters when not needed

## Additional Resources

- [Infrastructure README](../infrastructure/README.md) - Detailed infrastructure documentation
- [Pulumi GCP Documentation](https://www.pulumi.com/docs/clouds/gcp/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Workload Identity Guide](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Network Policies Guide](https://cloud.google.com/kubernetes-engine/docs/how-to/network-policy)

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review Pulumi logs: `pulumi logs`
3. Check GCP Console for cluster status
4. Review [Pulumi documentation](https://www.pulumi.com/docs/)
5. Check [GKE documentation](https://cloud.google.com/kubernetes-engine/docs)

