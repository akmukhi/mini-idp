# Kubernetes Components Usage Guide

This guide provides detailed instructions for deploying and using the core Kubernetes infrastructure components on your GKE cluster.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Component Details](#component-details)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Accessing Components](#accessing-components)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## Overview

The Kubernetes components infrastructure deploys five essential components:

1. **ArgoCD** - GitOps continuous delivery tool for automated deployments
2. **Prometheus + Grafana** - Monitoring and observability stack
3. **Fluent Bit** - Log aggregation and forwarding to GCP Cloud Logging
4. **External Secrets Operator** - Secure secret management with GCP Secret Manager
5. **cert-manager** - Automatic TLS certificate management

All components are deployed using Helm charts via Pulumi, ensuring infrastructure-as-code management.

## Prerequisites

Before deploying Kubernetes components:

1. **GKE cluster must be deployed** (see [GKE Infrastructure Guide](./gke-infrastructure.md))

2. **kubectl configured** to access your cluster:
   ```bash
   gcloud container clusters get-credentials CLUSTER_NAME \
     --region REGION \
     --project PROJECT_ID
   ```

3. **Verify cluster access:**
   ```bash
   kubectl get nodes
   ```

4. **Install dependencies:**
   ```bash
   cd infrastructure
   pip install -r requirements.txt
   ```

5. **Required GCP APIs enabled:**
   - Secret Manager API (for External Secrets Operator)
   ```bash
   gcloud services enable secretmanager.googleapis.com
   ```

## Component Details

### 1. ArgoCD

**Purpose**: GitOps continuous delivery tool that automatically syncs applications from Git repositories.

**Features**:
- Web UI for application management
- Automatic sync from Git
- Multi-cluster support
- RBAC integration

**Default Namespace**: `argocd`

### 2. Prometheus + Grafana Stack

**Purpose**: Comprehensive monitoring and observability solution.

**Components**:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and management

**Default Namespace**: `monitoring`

### 3. Fluent Bit

**Purpose**: Lightweight log processor and forwarder to GCP Cloud Logging.

**Features**:
- Log collection from pods
- Log parsing and filtering
- Forwarding to GCP Cloud Logging
- Workload Identity integration

**Default Namespace**: `logging`

### 4. External Secrets Operator

**Purpose**: Synchronizes secrets from external secret management systems (GCP Secret Manager) into Kubernetes.

**Features**:
- Automatic secret synchronization
- GCP Secret Manager integration
- Secret rotation support
- Workload Identity authentication

**Default Namespace**: `external-secrets-system`

### 5. cert-manager

**Purpose**: Automatic TLS certificate management and issuance.

**Features**:
- Let's Encrypt integration
- Automatic certificate renewal
- Multiple issuer types
- Cluster-wide and namespace-scoped issuers

**Default Namespace**: `cert-manager`

## Deployment

### Step 1: Set Up Workload Identity Service Accounts

Some components require Workload Identity service accounts for GCP authentication:

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

### Step 2: Bind Service Accounts to Kubernetes

```bash
PROJECT=$(pulumi config get gcp:project)

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

### Step 3: Configure Components (Optional)

```bash
cd infrastructure

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

### Step 4: Deploy Components

**Option A: Deploy as separate Pulumi program**

Create a new Pulumi stack for components:

```bash
cd infrastructure
pulumi stack init k8s-components
pulumi config set gcp:project YOUR_PROJECT_ID
pulumi preview --program k8s_components.py
pulumi up --program k8s_components.py
```

**Option B: Integrate into main program**

Modify `__main__.py` to import and call the components:

```python
# At the end of __main__.py
from k8s_components import *  # This will deploy all components
```

Then deploy:

```bash
pulumi up
```

### Step 5: Verify Deployment

```bash
# Check all namespaces
kubectl get namespaces | grep -E "argocd|monitoring|logging|cert-manager|external-secrets"

# Check pods in each namespace
kubectl get pods -n argocd
kubectl get pods -n monitoring
kubectl get pods -n logging
kubectl get pods -n cert-manager
kubectl get pods -n external-secrets-system
```

## Configuration

### ArgoCD Configuration

```bash
# Set admin password
pulumi config set components.argocd:adminPassword your-password

# Enable ingress
pulumi config set components.argocd:ingressEnabled true
pulumi config set components.argocd:ingressHost argocd.example.com

# Custom namespace
pulumi config set components.argocd:namespace custom-argocd
```

### Prometheus + Grafana Configuration

```bash
# Grafana admin password
pulumi config set components.prometheus:grafanaAdminPassword your-password

# Prometheus retention period
pulumi config set components.prometheus:prometheusRetention 30d

# Storage class for persistent volumes
pulumi config set components.prometheus:storageClass standard-rwo

# Custom namespace
pulumi config set components.prometheus:namespace custom-monitoring
```

### Fluent Bit Configuration

```bash
# Log level
pulumi config set components.fluentbit:logLevel info

# Custom namespace
pulumi config set components.fluentbit:namespace custom-logging
```

### External Secrets Configuration

```bash
# Enable/disable Secret Manager
pulumi config set components.external-secrets:secretManagerEnabled true

# Custom namespace
pulumi config set components.external-secrets:namespace custom-external-secrets
```

### cert-manager Configuration

```bash
# Let's Encrypt email
pulumi config set components.cert-manager:letsencryptEmail your-email@example.com

# Let's Encrypt server (staging or production)
pulumi config set components.cert-manager:letsencryptServer https://acme-v02.api.letsencrypt.org/directory

# Custom namespace
pulumi config set components.cert-manager:namespace custom-cert-manager
```

## Accessing Components

### ArgoCD

**Get LoadBalancer URL:**
```bash
kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

**Get initial admin password:**
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

**Access via port-forward (alternative):**
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Access at https://localhost:8080
```

**Login:**
- Username: `admin`
- Password: (from secret above or configured password)

### Grafana

**Get LoadBalancer URL:**
```bash
kubectl get svc -n monitoring grafana -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

**Default credentials:**
- Username: `admin`
- Password: (configured via `components.prometheus:grafanaAdminPassword`)

**Access via port-forward:**
```bash
kubectl port-forward svc/grafana -n monitoring 3000:80
# Access at http://localhost:3000
```

### Prometheus

**Get LoadBalancer URL:**
```bash
kubectl get svc -n monitoring prometheus-kube-prometheus-prometheus -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

**Access via port-forward:**
```bash
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
# Access at http://localhost:9090
```

## Usage Examples

### Using ArgoCD

**1. Add a Git repository:**
```bash
argocd repo add https://github.com/your-org/your-repo \
  --type git \
  --name your-repo
```

**2. Create an application:**
```bash
argocd app create my-app \
  --repo https://github.com/your-org/your-repo \
  --path manifests \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default
```

**3. Sync application:**
```bash
argocd app sync my-app
```

### Using External Secrets Operator

**1. Create a secret in GCP Secret Manager:**
```bash
echo -n "my-secret-value" | gcloud secrets create my-secret \
  --data-file=- \
  --project=YOUR_PROJECT_ID
```

**2. Create a SecretStore:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secret-store
  namespace: default
spec:
  provider:
    gcpsm:
      projectId: YOUR_PROJECT_ID
      auth:
        workloadIdentity:
          clusterLocation: REGION
          clusterName: CLUSTER_NAME
          serviceAccountRef:
            name: external-secrets
```

**3. Create an ExternalSecret:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-external-secret
  namespace: default
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcp-secret-store
    kind: SecretStore
  target:
    name: my-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: my-secret
```

### Using cert-manager

**1. Verify ClusterIssuer is created:**
```bash
kubectl get clusterissuer letsencrypt-prod
```

**2. Create a certificate:**
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: example-com
  namespace: default
spec:
  secretName: example-com-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - example.com
  - www.example.com
```

**3. Use certificate in Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - example.com
    secretName: example-com-tls
  rules:
  - host: example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: example-service
            port:
              number: 80
```

### Using Fluent Bit

Fluent Bit automatically collects logs from all pods and forwards them to GCP Cloud Logging. No additional configuration needed.

**View logs in GCP Console:**
- Navigate to [Cloud Logging](https://console.cloud.google.com/logs)
- Filter by resource type: `k8s_cluster` or `k8s_pod`

**Query logs via gcloud:**
```bash
gcloud logging read "resource.type=k8s_pod" --limit 50
```

## Troubleshooting

### Components Not Starting

**Check pod status:**
```bash
kubectl get pods -n NAMESPACE
kubectl describe pod POD_NAME -n NAMESPACE
kubectl logs POD_NAME -n NAMESPACE
```

**Common issues:**
- Insufficient resources: Check node capacity
- Image pull errors: Check network connectivity
- Config errors: Review Helm values

### Workload Identity Issues

**Verify service account binding:**
```bash
kubectl get serviceaccount -n NAMESPACE SERVICE_ACCOUNT_NAME -o yaml
```

**Check IAM bindings:**
```bash
gcloud iam service-accounts get-iam-policy SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com
```

### ArgoCD Access Issues

**Reset admin password:**
```bash
kubectl -n argocd patch secret argocd-secret \
  -p '{"stringData":{"admin.password":"$(argocd account bcrypt -p newpassword)"}}'
```

**Check ArgoCD server logs:**
```bash
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server
```

### Prometheus Not Scraping

**Check ServiceMonitor resources:**
```bash
kubectl get servicemonitor -n monitoring
```

**Check Prometheus targets:**
- Access Prometheus UI
- Navigate to Status > Targets
- Check for failed targets

### External Secrets Not Syncing

**Check SecretStore status:**
```bash
kubectl get secretstore -n NAMESPACE
kubectl describe secretstore SECRETSTORE_NAME -n NAMESPACE
```

**Check ExternalSecret status:**
```bash
kubectl get externalsecret -n NAMESPACE
kubectl describe externalsecret EXTERNAL_SECRET_NAME -n NAMESPACE
```

**Verify GCP Secret Manager access:**
```bash
gcloud secrets list --project=PROJECT_ID
```

### cert-manager Certificate Issues

**Check certificate status:**
```bash
kubectl get certificate -n NAMESPACE
kubectl describe certificate CERTIFICATE_NAME -n NAMESPACE
```

**Check certificate requests:**
```bash
kubectl get certificaterequest -n NAMESPACE
kubectl describe certificaterequest REQUEST_NAME -n NAMESPACE
```

**Check ClusterIssuer:**
```bash
kubectl get clusterissuer
kubectl describe clusterissuer letsencrypt-prod
```

## Best Practices

1. **Use separate namespaces** for each component (already configured)

2. **Set resource limits** to prevent resource exhaustion

3. **Enable monitoring** for all components via Prometheus

4. **Use Workload Identity** instead of service account keys

5. **Rotate secrets regularly** using External Secrets Operator

6. **Backup Grafana dashboards** and Prometheus data

7. **Use staging Let's Encrypt** for testing before production

8. **Configure alerts** in Alertmanager for critical issues

## Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Fluent Bit Documentation](https://docs.fluentbit.io/)
- [External Secrets Operator](https://external-secrets.io/)
- [cert-manager Documentation](https://cert-manager.io/docs/)

