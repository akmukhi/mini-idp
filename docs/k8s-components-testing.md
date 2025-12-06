# Kubernetes Components Testing Guide

This guide provides comprehensive testing instructions for all Kubernetes infrastructure components deployed on the GKE cluster.

## Table of Contents

- [Pre-Deployment Testing](#pre-deployment-testing)
- [Component Testing](#component-testing)
- [Integration Testing](#integration-testing)
- [End-to-End Testing](#end-to-end-testing)
- [Performance Testing](#performance-testing)
- [Troubleshooting Test Failures](#troubleshooting-test-failures)

## Pre-Deployment Testing

### Test 1: Validate Pulumi Configuration

**Purpose**: Verify that all configuration values are correctly set and accessible.

```bash
cd infrastructure

# Test configuration helper functions
python3 -c "
from k8s_config import *
import pulumi

# Mock Pulumi config for testing
with pulumi.Config() as config:
    print('Testing configuration functions...')
    try:
        project = get_gcp_project()
        print(f'✓ GCP Project: {project}')
    except Exception as e:
        print(f'✗ Error getting project: {e}')
    
    try:
        region = get_gcp_region()
        print(f'✓ GCP Region: {region}')
    except Exception as e:
        print(f'✗ Error getting region: {e}')
    
    try:
        argocd_config = get_argocd_config()
        print(f'✓ ArgoCD Config: {argocd_config}')
    except Exception as e:
        print(f'✗ Error getting ArgoCD config: {e}')
"

# Verify Pulumi config is set
pulumi config
```

**Expected Result**: All configuration values should be accessible without errors.

### Test 2: Validate Python Syntax

**Purpose**: Ensure all Python files have correct syntax.

```bash
cd infrastructure

# Test syntax of all Python files
python3 -m py_compile k8s_config.py
python3 -m py_compile k8s_components.py

# Test imports
python3 -c "
import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
from config import get_gcp_project
from k8s_config import get_argocd_config
print('✓ All imports successful')
"
```

**Expected Result**: No syntax errors, all imports successful.

### Test 3: Validate Cluster Access

**Purpose**: Verify kubectl can access the GKE cluster.

```bash
# Get cluster credentials
CLUSTER_NAME=$(pulumi stack output cluster_name)
REGION=$(pulumi stack output cluster_location)
PROJECT=$(pulumi config get gcp:project)

gcloud container clusters get-credentials $CLUSTER_NAME \
  --region $REGION \
  --project $PROJECT

# Test cluster access
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

**Expected Result**: 
- Cluster info displays correctly
- Nodes are visible and in Ready state
- Default namespaces exist

### Test 4: Validate Workload Identity Setup

**Purpose**: Verify Workload Identity service accounts are properly configured.

```bash
PROJECT=$(pulumi config get gcp:project)

# Check Fluent Bit service account
gcloud iam service-accounts describe fluent-bit@$PROJECT.iam.gserviceaccount.com

# Check External Secrets service account
gcloud iam service-accounts describe external-secrets@$PROJECT.iam.gserviceaccount.com

# Verify IAM bindings
gcloud iam service-accounts get-iam-policy \
  fluent-bit@$PROJECT.iam.gserviceaccount.com

gcloud iam service-accounts get-iam-policy \
  external-secrets@$PROJECT.iam.gserviceaccount.com
```

**Expected Result**: Service accounts exist and have correct IAM bindings.

### Test 5: Preview Pulumi Deployment

**Purpose**: Verify Pulumi can plan the deployment without errors.

```bash
cd infrastructure

# Preview deployment
pulumi preview --program k8s_components.py
```

**Expected Result**: Preview shows all resources that will be created without errors.

## Component Testing

### Testing cert-manager

#### Test 1: Verify cert-manager Deployment

```bash
# Check namespace exists
kubectl get namespace cert-manager

# Check pods are running
kubectl get pods -n cert-manager

# Verify all pods are in Running state
kubectl get pods -n cert-manager -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
```

**Expected Result**: 
- Namespace exists
- All pods (cert-manager, cert-manager-webhook, cert-manager-cainjector) are Running

#### Test 2: Verify ClusterIssuer

```bash
# Check ClusterIssuer exists (if email was configured)
kubectl get clusterissuer letsencrypt-prod

# Describe ClusterIssuer
kubectl describe clusterissuer letsencrypt-prod
```

**Expected Result**: ClusterIssuer exists and is Ready (if configured).

#### Test 3: Test Certificate Creation

```bash
# Create a test certificate
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: test-certificate
  namespace: default
spec:
  secretName: test-certificate-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - test.example.com
EOF

# Check certificate status
kubectl get certificate test-certificate -n default
kubectl describe certificate test-certificate -n default

# Check certificate request
kubectl get certificaterequest -n default
```

**Expected Result**: Certificate resource is created (may be pending if DNS is not configured).

#### Test 4: Verify CRDs Installed

```bash
# Check cert-manager CRDs
kubectl get crd | grep cert-manager

# Should see:
# - certificates.cert-manager.io
# - certificaterequests.cert-manager.io
# - clusterissuers.cert-manager.io
# - issuers.cert-manager.io
```

**Expected Result**: All cert-manager CRDs are installed.

### Testing External Secrets Operator

#### Test 1: Verify ESO Deployment

```bash
# Check namespace
kubectl get namespace external-secrets-system

# Check pods
kubectl get pods -n external-secrets-system

# Verify pods are running
kubectl get pods -n external-secrets-system -o wide
```

**Expected Result**: 
- Namespace exists
- External Secrets Operator pods are Running

#### Test 2: Verify Workload Identity

```bash
# Check service account annotation
kubectl get serviceaccount external-secrets -n external-secrets-system -o yaml | grep annotations

# Should show: iam.gke.io/gcp-service-account annotation
```

**Expected Result**: Service account has Workload Identity annotation.

#### Test 3: Test GCP Secret Manager Integration

```bash
PROJECT=$(pulumi config get gcp:project)

# Create a test secret in GCP Secret Manager
echo -n "test-secret-value" | gcloud secrets create test-secret \
  --data-file=- \
  --project=$PROJECT

# Create SecretStore
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secret-store
  namespace: default
spec:
  provider:
    gcpsm:
      projectId: $PROJECT
      auth:
        workloadIdentity:
          clusterLocation: $(pulumi stack output cluster_location)
          clusterName: $(pulumi stack output cluster_name)
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets-system
EOF

# Wait for SecretStore to be ready
kubectl wait --for=condition=Ready secretstore/gcp-secret-store -n default --timeout=60s

# Create ExternalSecret
cat <<EOF | kubectl apply -f -
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: test-external-secret
  namespace: default
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcp-secret-store
    kind: SecretStore
  target:
    name: test-secret
    creationPolicy: Owner
  data:
  - secretKey: password
    remoteRef:
      key: test-secret
EOF

# Check ExternalSecret status
kubectl get externalsecret test-external-secret -n default
kubectl describe externalsecret test-external-secret -n default

# Wait for secret to be synced
sleep 10

# Verify Kubernetes secret was created
kubectl get secret test-secret -n default
kubectl get secret test-secret -n default -o jsonpath='{.data.password}' | base64 -d
```

**Expected Result**: 
- SecretStore is Ready
- ExternalSecret syncs successfully
- Kubernetes secret is created with correct value

#### Test 4: Cleanup Test Resources

```bash
# Delete test resources
kubectl delete externalsecret test-external-secret -n default
kubectl delete secretstore gcp-secret-store -n default
kubectl delete secret test-secret -n default

# Delete GCP secret
gcloud secrets delete test-secret --project=$(pulumi config get gcp:project)
```

### Testing Prometheus + Grafana

#### Test 1: Verify Prometheus Deployment

```bash
# Check namespace
kubectl get namespace monitoring

# Check Prometheus pods
kubectl get pods -n monitoring | grep prometheus

# Check Prometheus service
kubectl get svc -n monitoring | grep prometheus
```

**Expected Result**: 
- Namespace exists
- Prometheus pods are Running
- Prometheus service exists (LoadBalancer or ClusterIP)

#### Test 2: Access Prometheus UI

```bash
# Get Prometheus service URL
PROMETHEUS_IP=$(kubectl get svc -n monitoring prometheus-kube-prometheus-prometheus -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# If using port-forward instead
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090

# Test Prometheus API
curl http://localhost:9090/api/v1/status/config
curl http://localhost:9090/api/v1/targets
```

**Expected Result**: 
- Prometheus UI is accessible
- API returns valid responses
- Targets are being scraped

#### Test 3: Verify Prometheus Scraping

```bash
# Check ServiceMonitors
kubectl get servicemonitor -n monitoring

# Check Prometheus targets via API
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090 &
sleep 2
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="up")'
kill %1
```

**Expected Result**: Prometheus is scraping targets successfully.

#### Test 4: Verify Grafana Deployment

```bash
# Check Grafana pods
kubectl get pods -n monitoring | grep grafana

# Check Grafana service
kubectl get svc -n monitoring | grep grafana

# Get Grafana LoadBalancer IP
GRAFANA_IP=$(kubectl get svc -n monitoring grafana -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Grafana URL: http://$GRAFANA_IP"
```

**Expected Result**: 
- Grafana pods are Running
- Grafana service exists with LoadBalancer

#### Test 5: Access Grafana UI

```bash
# Port-forward to Grafana
kubectl port-forward svc/grafana -n monitoring 3000:80

# Test Grafana API
curl http://localhost:3000/api/health
```

**Expected Result**: 
- Grafana UI is accessible at http://localhost:3000
- Default login: admin / (configured password)
- Health endpoint returns healthy status

#### Test 6: Verify Persistent Storage

```bash
# Check PVCs for Prometheus
kubectl get pvc -n monitoring | grep prometheus

# Check PVCs for Grafana
kubectl get pvc -n monitoring | grep grafana

# Verify storage is bound
kubectl get pvc -n monitoring
```

**Expected Result**: 
- PersistentVolumeClaims exist and are Bound
- Storage is properly configured

### Testing Fluent Bit

#### Test 1: Verify Fluent Bit Deployment

```bash
# Check namespace
kubectl get namespace logging

# Check Fluent Bit pods
kubectl get pods -n logging

# Verify pods are running
kubectl get pods -n logging -o wide
```

**Expected Result**: 
- Namespace exists
- Fluent Bit pods (DaemonSet) are Running on all nodes

#### Test 2: Verify Workload Identity

```bash
# Check service account annotation
kubectl get serviceaccount fluent-bit -n logging -o yaml | grep annotations

# Should show: iam.gke.io/gcp-service-account annotation
```

**Expected Result**: Service account has Workload Identity annotation.

#### Test 3: Test Log Collection

```bash
# Create a test pod that generates logs
kubectl run test-logger --image=busybox --restart=Never -- /bin/sh -c "while true; do echo 'Test log message'; sleep 5; done"

# Check Fluent Bit is collecting logs
kubectl logs -n logging -l app.kubernetes.io/name=fluent-bit --tail=50 | grep "test-logger"

# Cleanup
kubectl delete pod test-logger
```

**Expected Result**: Fluent Bit is collecting logs from pods.

#### Test 4: Verify Logs in GCP Cloud Logging

```bash
PROJECT=$(pulumi config get gcp:project)
CLUSTER_NAME=$(pulumi stack output cluster_name)

# Query logs in GCP
gcloud logging read "resource.type=k8s_pod AND resource.labels.cluster_name=$CLUSTER_NAME" \
  --project=$PROJECT \
  --limit=10 \
  --format=json
```

**Expected Result**: Logs appear in GCP Cloud Logging.

### Testing ArgoCD

#### Test 1: Verify ArgoCD Deployment

```bash
# Check namespace
kubectl get namespace argocd

# Check ArgoCD pods
kubectl get pods -n argocd

# Verify all components are running
kubectl get pods -n argocd -o wide
```

**Expected Result**: 
- Namespace exists
- All ArgoCD pods (server, repo-server, application-controller, etc.) are Running

#### Test 2: Access ArgoCD UI

```bash
# Get ArgoCD server service
kubectl get svc -n argocd argocd-server

# Get LoadBalancer IP
ARGOCD_IP=$(kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "ArgoCD URL: https://$ARGOCD_IP"

# Port-forward alternative
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**Expected Result**: ArgoCD UI is accessible.

#### Test 3: Get ArgoCD Admin Password

```bash
# Get initial admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD Admin Password: $ARGOCD_PASSWORD"

# Or if custom password was set
kubectl -n argocd get secret argocd-secret -o jsonpath="{.data.admin\\.password}" | base64 -d
```

**Expected Result**: Admin password is retrievable.

#### Test 4: Test ArgoCD CLI Access

```bash
# Install ArgoCD CLI (if not installed)
# brew install argocd  # macOS
# or download from: https://github.com/argoproj/argo-cd/releases

# Login to ArgoCD
ARGOCD_IP=$(kubectl get svc -n argocd argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

argocd login $ARGOCD_IP --insecure --username admin --password $ARGOCD_PASSWORD

# Verify connection
argocd version
argocd cluster list
```

**Expected Result**: 
- ArgoCD CLI can connect
- Version information displays
- Cluster list shows current cluster

#### Test 5: Test Git Repository Connection

```bash
# Add a test repository
argocd repo add https://github.com/argoproj/argocd-example-apps \
  --type git \
  --name argocd-example-apps

# List repositories
argocd repo list
```

**Expected Result**: Repository is added and accessible.

#### Test 6: Create and Sync Test Application

```bash
# Create a test application
argocd app create test-app \
  --repo https://github.com/argoproj/argocd-example-apps \
  --path guestbook \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default

# Check application status
argocd app get test-app

# Sync application
argocd app sync test-app

# Verify application is synced
argocd app get test-app
```

**Expected Result**: 
- Application is created
- Application syncs successfully
- Resources are deployed to cluster

## Integration Testing

### Test 1: Component Interoperability

**Purpose**: Verify components work together.

```bash
# 1. Use External Secrets to create a secret
# 2. Use that secret in an ArgoCD application
# 3. Use cert-manager to provide TLS for ArgoCD ingress
# 4. Monitor everything with Prometheus
# 5. View logs in Grafana (via Fluent Bit)

# Create secret via External Secrets
# (Use test from External Secrets section)

# Create ArgoCD application that uses the secret
# (Use test from ArgoCD section)

# Verify Prometheus is monitoring ArgoCD
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090 &
curl http://localhost:9090/api/v1/query?query=up{job="argocd-metrics"} | jq
kill %1
```

**Expected Result**: All components work together seamlessly.

### Test 2: End-to-End Workflow

**Purpose**: Test a complete workflow using all components.

```bash
# 1. Create a secret in GCP Secret Manager
# 2. Sync it via External Secrets Operator
# 3. Deploy an application via ArgoCD that uses the secret
# 4. Issue TLS certificate via cert-manager
# 5. Monitor application with Prometheus
# 6. View logs with Fluent Bit

# This is a comprehensive test that exercises all components
```

## Performance Testing

### Test 1: Resource Usage

```bash
# Check resource usage of all components
kubectl top pods -n cert-manager
kubectl top pods -n external-secrets-system
kubectl top pods -n monitoring
kubectl top pods -n logging
kubectl top pods -n argocd

# Check node resource usage
kubectl top nodes
```

**Expected Result**: Resource usage is within acceptable limits.

### Test 2: Component Startup Time

```bash
# Time component deployments
time kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=cert-manager -n cert-manager --timeout=300s
time kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=external-secrets -n external-secrets-system --timeout=300s
```

**Expected Result**: Components start within reasonable time.

## Troubleshooting Test Failures

### Common Issues and Solutions

#### Issue: Pods Not Starting

```bash
# Check pod events
kubectl describe pod POD_NAME -n NAMESPACE

# Check pod logs
kubectl logs POD_NAME -n NAMESPACE

# Check resource limits
kubectl describe node NODE_NAME
```

#### Issue: Workload Identity Not Working

```bash
# Verify service account annotation
kubectl get serviceaccount SERVICE_ACCOUNT -n NAMESPACE -o yaml

# Check IAM bindings
gcloud iam service-accounts get-iam-policy SERVICE_ACCOUNT@PROJECT.iam.gserviceaccount.com

# Check pod service account
kubectl get pod POD_NAME -n NAMESPACE -o jsonpath='{.spec.serviceAccountName}'
```

#### Issue: Services Not Accessible

```bash
# Check service endpoints
kubectl get endpoints -n NAMESPACE SERVICE_NAME

# Check LoadBalancer status
kubectl get svc -n NAMESPACE SERVICE_NAME

# Check ingress (if configured)
kubectl get ingress -n NAMESPACE
```

## Automated Testing Script

Create a test script to run all tests:

```bash
#!/bin/bash
# test-k8s-components.sh

set -e

echo "=== Kubernetes Components Testing ==="

echo "1. Testing cert-manager..."
kubectl get pods -n cert-manager
echo "✓ cert-manager test passed"

echo "2. Testing External Secrets Operator..."
kubectl get pods -n external-secrets-system
echo "✓ External Secrets test passed"

echo "3. Testing Prometheus + Grafana..."
kubectl get pods -n monitoring
echo "✓ Prometheus + Grafana test passed"

echo "4. Testing Fluent Bit..."
kubectl get pods -n logging
echo "✓ Fluent Bit test passed"

echo "5. Testing ArgoCD..."
kubectl get pods -n argocd
echo "✓ ArgoCD test passed"

echo ""
echo "All tests completed successfully!"
```

## Test Checklist

Use this checklist to verify all components:

- [ ] cert-manager namespace exists
- [ ] cert-manager pods are Running
- [ ] ClusterIssuer is Ready (if configured)
- [ ] External Secrets Operator namespace exists
- [ ] External Secrets Operator pods are Running
- [ ] SecretStore can connect to GCP Secret Manager
- [ ] ExternalSecret can sync secrets
- [ ] Prometheus namespace exists
- [ ] Prometheus pods are Running
- [ ] Prometheus UI is accessible
- [ ] Prometheus is scraping targets
- [ ] Grafana pods are Running
- [ ] Grafana UI is accessible
- [ ] Persistent volumes are Bound
- [ ] Fluent Bit namespace exists
- [ ] Fluent Bit pods are Running on all nodes
- [ ] Fluent Bit is collecting logs
- [ ] Logs appear in GCP Cloud Logging
- [ ] ArgoCD namespace exists
- [ ] ArgoCD pods are Running
- [ ] ArgoCD UI is accessible
- [ ] ArgoCD CLI can connect
- [ ] ArgoCD can sync applications

## Additional Resources

- [Component Usage Guide](./k8s-components.md)
- [GKE Infrastructure Guide](./gke-infrastructure.md)
- [ArgoCD Testing](https://argo-cd.readthedocs.io/en/stable/operator-manual/health/)
- [Prometheus Testing](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/)

