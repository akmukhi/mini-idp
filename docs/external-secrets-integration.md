# External Secrets Operator Integration

Mini-IDP automatically integrates with External Secrets Operator to securely inject secrets from GCP Secret Manager into your Kubernetes deployments. Secrets are automatically synced and kept up-to-date without manual intervention.

## Overview

When you deploy applications with External Secrets:

- **Automatic Secret Sync** - Secrets are automatically synced from GCP Secret Manager
- **Secure Injection** - Secrets are injected into pods via Kubernetes Secrets
- **Automatic Refresh** - Secrets are refreshed automatically at configured intervals
- **Workload Identity** - Uses GCP Workload Identity for secure authentication
- **Zero Configuration** - Works out of the box with sensible defaults

## How It Works

### Architecture

```
┌─────────────────┐
│  GCP Secret     │
│  Manager        │
│  (Secrets)      │
└────────┬────────┘
         │
         │ Workload Identity
         ▼
┌─────────────────┐
│  External       │
│  Secrets        │
│  Operator       │
└────────┬────────┘
         │
         │ Syncs Secrets
         ▼
┌─────────────────┐
│  Kubernetes     │
│  Secret         │
│  (in namespace) │
└────────┬────────┘
         │
         │ Mounted/Injected
         ▼
┌─────────────────┐
│  Your Pods      │
│  (Applications) │
└─────────────────┘
```

### Automatic Configuration

Mini-IDP automatically:

1. **Generates ExternalSecret Resources** - Custom resources that define what secrets to sync
2. **Creates Kubernetes Secrets** - External Secrets Operator creates standard Kubernetes Secrets
3. **Injects into Pods** - Secrets are referenced in deployments via `secretKeyRef`

## Usage

### Basic Usage

Sync a secret from GCP Secret Manager:

```bash
# Deploy with External Secret
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --external-secret database-password

# This creates an ExternalSecret that syncs:
# - GCP Secret: database-password
# - Kubernetes Secret: my-api-secrets
# - Secret Key: database-password (same as GCP secret name)
```

### Custom Secret Key

Map GCP secret to a different Kubernetes secret key:

```bash
# Map GCP secret 'db-credentials' to Kubernetes key 'PASSWORD'
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --external-secret db-credentials:PASSWORD
```

### Multiple Secrets

Sync multiple secrets:

```bash
# Sync multiple secrets
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --external-secret database-password \
  --external-secret api-key:API_KEY \
  --external-secret jwt-secret
```

### Custom Secret Store

Use a custom SecretStore:

```bash
# Use custom SecretStore
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --external-secret my-secret \
  --secret-store my-custom-store
```

### Custom Refresh Interval

Change secret refresh interval:

```bash
# Refresh secrets every 30 minutes
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --external-secret my-secret \
  --secret-refresh-interval 30m
```

## Secret Format

### External Secret Format

The `--external-secret` flag accepts two formats:

1. **Simple format**: `GCP_SECRET_NAME`
   - Syncs entire secret
   - Kubernetes key = GCP secret name

2. **Key mapping format**: `GCP_SECRET_NAME:K8S_SECRET_KEY`
   - Maps specific GCP secret to Kubernetes key
   - Useful for renaming or extracting specific values

### Examples

```bash
# Simple: Sync entire secret 'db-password'
--external-secret db-password

# Key mapping: Map 'db-credentials' GCP secret to 'PASSWORD' key
--external-secret db-credentials:PASSWORD

# Multiple secrets
--external-secret db-password \
--external-secret api-key:API_KEY \
--external-secret jwt-secret:JWT_SECRET
```

## Generated Resources

### ExternalSecret Resource

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: my-api-database-password
  namespace: production
  labels:
    app: my-api
    managed-by: mini-idp
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: gcp-secret-store
    kind: SecretStore
  target:
    name: my-api-secrets
    creationPolicy: Owner
  data:
  - secretKey: PASSWORD
    remoteRef:
      key: database-password
```

### Kubernetes Secret

External Secrets Operator automatically creates:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-api-secrets
  namespace: production
type: Opaque
data:
  PASSWORD: <base64-encoded-value>
```

### Deployment Reference

Secrets are automatically referenced in deployments:

```yaml
env:
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: my-api-secrets
      key: PASSWORD
```

## SecretStore Setup

### Default SecretStore

A default SecretStore named `gcp-secret-store` should be created in your namespace. Create it manually:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secret-store
  namespace: default
spec:
  provider:
    gcpsm:
      projectId: your-gcp-project
      auth:
        workloadIdentity:
          clusterLocation: us-central1
          clusterName: your-cluster
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets-system
```

### Creating SecretStore via CLI

You can create a SecretStore helper script:

```bash
# Create SecretStore for a namespace
kubectl apply -f - <<EOF
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: gcp-secret-store
  namespace: production
spec:
  provider:
    gcpsm:
      projectId: $(gcloud config get-value project)
      auth:
        workloadIdentity:
          clusterLocation: us-central1
          clusterName: my-cluster
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets-system
EOF
```

## GCP Secret Manager Setup

### Creating Secrets in GCP

```bash
# Create a secret
echo -n "my-secret-value" | gcloud secrets create my-secret \
  --data-file=- \
  --replication-policy="automatic"

# Create secret with multiple keys (JSON)
echo '{"username":"admin","password":"secret123"}' | \
  gcloud secrets create db-credentials \
  --data-file=-

# Grant access to External Secrets service account
gcloud secrets add-iam-policy-binding my-secret \
  --member="serviceAccount:external-secrets@PROJECT.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Secret Versions

External Secrets Operator syncs the latest version by default. To pin to a specific version:

```yaml
spec:
  data:
  - secretKey: PASSWORD
    remoteRef:
      key: database-password
      version: "1"  # Pin to version 1
```

## Best Practices

### 1. Use Environment-Specific Secrets

Create separate secrets for each environment:

```bash
# Production secrets
--external-secret prod-db-password

# Staging secrets
--external-secret staging-db-password
```

### 2. Set Appropriate Refresh Intervals

- **Frequently rotated secrets**: 15m or 30m
- **Standard secrets**: 1h (default)
- **Rarely changed secrets**: 24h

### 3. Use Secret Key Mapping

Map GCP secrets to meaningful Kubernetes keys:

```bash
# Instead of using GCP secret name directly
--external-secret db-credentials:DATABASE_PASSWORD
--external-secret db-credentials:DATABASE_USER
```

### 4. Organize Secrets

Group related secrets in the same Kubernetes Secret:

```bash
# All database secrets in one Kubernetes Secret
--external-secret db-host:DATABASE_HOST
--external-secret db-password:DATABASE_PASSWORD
--external-secret db-user:DATABASE_USER
# All map to 'my-api-secrets' Kubernetes Secret
```

### 5. Rotate Secrets Regularly

- Use GCP Secret Manager's rotation features
- External Secrets Operator automatically picks up new versions
- Set shorter refresh intervals for critical secrets

## Troubleshooting

### Secrets Not Syncing

1. **Check ExternalSecret status:**
   ```bash
   kubectl get externalsecret -n <namespace>
   kubectl describe externalsecret <name> -n <namespace>
   ```

2. **Check SecretStore:**
   ```bash
   kubectl get secretstore -n <namespace>
   kubectl describe secretstore gcp-secret-store -n <namespace>
   ```

3. **Verify GCP Secret exists:**
   ```bash
   gcloud secrets list
   gcloud secrets describe <secret-name>
   ```

4. **Check External Secrets Operator logs:**
   ```bash
   kubectl logs -n external-secrets-system -l app.kubernetes.io/name=external-secrets
   ```

### Permission Errors

1. **Verify Workload Identity binding:**
   ```bash
   kubectl get serviceaccount external-secrets -n external-secrets-system -o yaml
   ```

2. **Check IAM permissions:**
   ```bash
   gcloud projects get-iam-policy <project> \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:external-secrets@*"
   ```

3. **Verify Secret Manager API is enabled:**
   ```bash
   gcloud services list --enabled | grep secretmanager
   ```

### Secret Not Found

- Verify secret name matches exactly (case-sensitive)
- Check secret exists in the correct GCP project
- Ensure secret has been granted access to External Secrets service account

## Advanced Configuration

### Multiple Secret Keys from One GCP Secret

If your GCP secret is JSON with multiple keys:

```yaml
# GCP Secret: db-credentials
# Value: {"username":"admin","password":"secret123"}

# Create multiple ExternalSecrets
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
spec:
  data:
  - secretKey: DATABASE_USER
    remoteRef:
      key: db-credentials
      property: username
  - secretKey: DATABASE_PASSWORD
    remoteRef:
      key: db-credentials
      property: password
```

### Secret Rotation

External Secrets Operator automatically picks up new secret versions:

1. Create new version in GCP Secret Manager
2. External Secrets Operator syncs on next refresh interval
3. Pods automatically get new secret values on restart

### Namespace Isolation

Create separate SecretStores per namespace for isolation:

```bash
# Production namespace
--secret-store prod-secret-store

# Staging namespace
--secret-store staging-secret-store
```

## Integration with Deployments

### Automatic Secret Injection

When you use `--external-secret`, the generated deployment automatically references the synced Kubernetes Secret:

```yaml
env:
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: my-api-secrets
      key: PASSWORD
```

### Using Secrets in Environment Variables

The `--secret` flag works with External Secrets:

```bash
# Use External Secret in environment variable
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --external-secret db-password:PASSWORD \
  --secret my-api-secrets:PASSWORD
```

## See Also

- [Kubernetes Components Documentation](k8s-components.md) - External Secrets Operator setup
- [GCP Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [External Secrets Operator Documentation](https://external-secrets.io/)

