# GKE Cluster Infrastructure

This directory contains Pulumi infrastructure code to provision a Google Kubernetes Engine (GKE) cluster with the following features:

- **Autoscaling Node Pools**: Automatically scales nodes based on workload demand
- **Workload Identity**: Enables secure pod-to-GCP service authentication
- **Network Policies**: Configures network policy enforcement for pod-to-pod communication
- **Monitoring/Logging**: Enables Google Cloud Monitoring and Logging

## Prerequisites

Before deploying this infrastructure, ensure you have:

1. **Pulumi CLI installed**
   ```bash
   curl -fsSL https://get.pulumi.com | sh
   ```

2. **GCP Project with billing enabled**
   - Create a project in [Google Cloud Console](https://console.cloud.google.com/)
   - Enable billing for the project

3. **gcloud CLI configured**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

4. **Python 3.12+** (matching project Python version)

5. **Required GCP APIs enabled** (will be enabled automatically by Pulumi):
   - Compute Engine API
   - Kubernetes Engine API
   - Cloud Monitoring API
   - Cloud Logging API

## Installation

1. **Navigate to the infrastructure directory:**
   ```bash
   cd infrastructure
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Configure Pulumi using command-line config commands (no YAML stack files required):

1. **Set GCP project ID (required):**
   ```bash
   pulumi config set gcp:project YOUR_PROJECT_ID
   ```

2. **Set GCP region (optional, defaults to us-central1):**
   ```bash
   pulumi config set gcp:region us-west1
   ```

3. **Set cluster name (optional, defaults to mini-idp-cluster):**
   ```bash
   pulumi config set cluster:name my-cluster-name
   ```

4. **Configure node pool (optional):**
   ```bash
   # Machine type (default: e2-medium)
   pulumi config set nodePool:machineType e2-standard-4
   
   # Min nodes (default: 1)
   pulumi config set nodePool:minNodes 2
   
   # Max nodes (default: 3)
   pulumi config set nodePool:maxNodes 5
   
   # Disk size in GB (default: 20)
   pulumi config set nodePool:diskSizeGb 50
   
   # Disk type (default: pd-standard)
   pulumi config set nodePool:diskType pd-ssd
   ```

5. **View current configuration:**
   ```bash
   pulumi config
   ```

## Deployment

1. **Preview changes:**
   ```bash
   pulumi preview
   ```
   This shows what resources will be created without making any changes.

2. **Deploy the infrastructure:**
   ```bash
   pulumi up
   ```
   Review the changes and type `yes` to proceed.

3. **Get cluster credentials:**
   After deployment, configure kubectl:
   ```bash
   gcloud container clusters get-credentials $(pulumi stack output cluster_name) \
     --region $(pulumi stack output cluster_location) \
     --project $(pulumi config get gcp:project)
   ```

4. **Verify cluster is running:**
   ```bash
   kubectl get nodes
   kubectl get pods --all-namespaces
   ```

## Infrastructure Components

### GKE Cluster

- **Workload Identity**: Enabled for secure authentication
- **Network Policies**: Enabled with Calico provider
- **Monitoring**: Cloud Monitoring enabled
- **Logging**: Cloud Logging enabled
- **Auto-upgrade**: Enabled for node pools
- **Auto-repair**: Enabled for node pools

### Node Pool

- **Autoscaling**: Configured with min/max node counts
- **Machine Type**: Configurable (default: e2-medium)
- **Disk**: Configurable size and type
- **Workload Identity**: Enabled on nodes

### Network

- Uses default VPC network
- Network policies enforced at pod level

## Outputs

After deployment, the following outputs are available:

```bash
# Get cluster name
pulumi stack output cluster_name

# Get cluster endpoint
pulumi stack output cluster_endpoint

# Get workload identity pool
pulumi stack output cluster_workload_identity_pool
```

## Updating Configuration

To update the cluster configuration:

1. Modify the configuration:
   ```bash
   pulumi config set nodePool:maxNodes 10
   ```

2. Preview changes:
   ```bash
   pulumi preview
   ```

3. Apply changes:
   ```bash
   pulumi up
   ```

## Destroying Infrastructure

To destroy all resources:

```bash
pulumi destroy
```

**Warning**: This will delete the entire GKE cluster and all associated resources. Make sure you have backups of any important data.

## Troubleshooting

### Authentication Issues

If you encounter authentication errors:

```bash
gcloud auth application-default login
```

### API Not Enabled

If you see API errors, the Pulumi code will automatically enable required APIs. If issues persist:

```bash
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

### Insufficient Permissions

Ensure your GCP account has the following roles:
- `roles/container.admin`
- `roles/compute.admin`
- `roles/iam.serviceAccountUser`
- `roles/serviceusage.serviceUsageAdmin`

### Network Policy Issues

If network policies are blocking traffic, you may need to create NetworkPolicy resources in Kubernetes to allow specific traffic patterns.

## Cost Considerations

- **Cluster**: GKE cluster management fee (~$73/month per cluster)
- **Nodes**: Based on machine type and number of nodes
- **Storage**: Based on disk size and type
- **Network**: Egress charges apply
- **Monitoring/Logging**: Free tier available, charges apply for high volume

Use the [GCP Pricing Calculator](https://cloud.google.com/products/calculator) to estimate costs.

## Kubernetes Components

After deploying the GKE cluster, you can deploy essential Kubernetes infrastructure components using the `k8s_components.py` program.

### Available Components

1. **ArgoCD** - GitOps continuous delivery tool
2. **Prometheus + Grafana** - Monitoring and observability stack
3. **Fluent Bit** - Log aggregation and forwarding to GCP Cloud Logging
4. **External Secrets Operator** - Integration with GCP Secret Manager
5. **cert-manager** - TLS certificate management with Let's Encrypt

### Deploying Kubernetes Components

1. **Ensure cluster is deployed and kubectl is configured:**
   ```bash
   kubectl get nodes
   ```

2. **Install additional dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure component settings (optional):**
   ```bash
   # ArgoCD configuration
   pulumi config set components.argocd:adminPassword your-secure-password
   pulumi config set components.argocd:ingressEnabled true
   pulumi config set components.argocd:ingressHost argocd.yourdomain.com
   
   # Prometheus/Grafana configuration
   pulumi config set components.prometheus:grafanaAdminPassword your-password
   pulumi config set components.prometheus:prometheusRetention 30d
   
   # cert-manager configuration
   pulumi config set components.cert-manager:letsencryptEmail your-email@example.com
   ```

4. **Deploy components:**
   ```bash
   # Option 1: Run as separate Pulumi program
   pulumi up --program k8s_components.py
   
   # Option 2: Import into main program (modify __main__.py)
   ```

5. **Access the components:**
   ```bash
   # Get ArgoCD LoadBalancer URL
   kubectl get svc -n argocd argocd-server
   
   # Get Grafana LoadBalancer URL
   kubectl get svc -n monitoring grafana
   
   # Get Prometheus LoadBalancer URL
   kubectl get svc -n monitoring prometheus-kube-prometheus-prometheus
   ```

### Component Configuration

All components support configuration via Pulumi config:

- **Helm chart versions**: `components.<component>:chartVersion`
- **Namespaces**: `components.<component>:namespace`
- **Component-specific settings**: See `k8s_config.py` for details

### Workload Identity Setup

Some components (Fluent Bit, External Secrets Operator) require Workload Identity service accounts. Create them before deployment:

```bash
PROJECT=$(pulumi config get gcp:project)

# Fluent Bit service account
gcloud iam service-accounts create fluent-bit \
  --project=$PROJECT \
  --display-name="Fluent Bit Service Account"

gcloud projects add-iam-policy-binding $PROJECT \
  --member="serviceAccount:fluent-bit@$PROJECT.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# External Secrets service account
gcloud iam service-accounts create external-secrets \
  --project=$PROJECT \
  --display-name="External Secrets Operator Service Account"

gcloud projects add-iam-policy-binding $PROJECT \
  --member="serviceAccount:external-secrets@$PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Then bind them to Kubernetes service accounts:

```bash
# Fluent Bit binding
gcloud iam service-accounts add-iam-policy-binding \
  fluent-bit@$PROJECT.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$PROJECT.svc.id.goog[logging/fluent-bit]"

# External Secrets binding
gcloud iam service-accounts add-iam-policy-binding \
  external-secrets@$PROJECT.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:$PROJECT.svc.id.goog[external-secrets-system/external-secrets]"
```

For detailed usage instructions, see [Kubernetes Components Documentation](../docs/k8s-components.md).

## Additional Resources

- [Pulumi GCP Documentation](https://www.pulumi.com/docs/clouds/gcp/)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
- [Network Policies](https://cloud.google.com/kubernetes-engine/docs/how-to/network-policy)
- [Kubernetes Components Documentation](../docs/k8s-components.md)

