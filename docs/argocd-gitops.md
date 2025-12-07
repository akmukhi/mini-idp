# ArgoCD GitOps Integration

Mini-IDP automatically generates ArgoCD Application resources for GitOps workflows. Deployments are managed declaratively through Git repositories, enabling version control, audit trails, and automated synchronization.

## Overview

When you deploy applications with GitOps enabled:

- **Automatic Application Generation** - ArgoCD Application resources created automatically
- **Git-Based Configuration** - All manifests stored in Git repositories
- **Automatic Synchronization** - ArgoCD automatically syncs changes from Git
- **Self-Healing** - ArgoCD automatically corrects drift from Git state
- **Audit Trail** - All changes tracked in Git history

## How It Works

### GitOps Architecture

```
┌─────────────────┐
│  Git Repository │
│  (Manifests)    │
└────────┬────────┘
         │
         │ ArgoCD Watches
         ▼
┌─────────────────┐
│  ArgoCD         │
│  (Controller)   │
└────────┬────────┘
         │
         │ Applies Manifests
         ▼
┌─────────────────┐
│  Kubernetes     │
│  Cluster        │
│  (Resources)    │
└─────────────────┘
```

### Workflow

1. **Generate Manifests** - Mini-IDP generates Kubernetes resources
2. **Commit to Git** - Manifests are committed to your Git repository
3. **ArgoCD Syncs** - ArgoCD Application watches the repository
4. **Automatic Deployment** - ArgoCD applies manifests to the cluster
5. **Continuous Monitoring** - ArgoCD ensures cluster matches Git state

## Usage

### Basic GitOps Deployment

```bash
# Deploy with GitOps (manifests applied directly, ArgoCD Application created)
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api
```

### Write Manifests to Directory

Generate manifests without applying them:

```bash
# Generate manifests to directory
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --write-manifests ./manifests/my-api

# Manifests are written to ./manifests/my-api/
# Commit them to Git manually
git add manifests/my-api
git commit -m "Add my-api deployment"
git push
```

### Custom Git Branch

```bash
# Use a specific branch
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api \
  --git-branch production
```

### Custom ArgoCD Project

```bash
# Use a custom ArgoCD project
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api \
  --argocd-project production
```

### Manual Sync (No Auto-Sync)

```bash
# Disable automatic sync (manual sync only)
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api \
  --no-auto-sync
```

### Disable Pruning

```bash
# Keep resources that are removed from Git
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api \
  --no-prune
```

### Disable Self-Healing

```bash
# Don't automatically correct drift
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api \
  --no-self-heal
```

## Generated Resources

### ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-api
  namespace: argocd
  labels:
    app: my-api
    managed-by: mini-idp
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo
    targetRevision: main
    path: manifests/my-api
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Git Repository Structure

### Recommended Structure

```
my-repo/
├── manifests/
│   ├── production/
│   │   ├── my-api/
│   │   │   ├── 00-deployment-my-api.yaml
│   │   │   ├── 01-service-my-api.yaml
│   │   │   ├── 02-hpa-my-api.yaml
│   │   │   └── 03-servicemonitor-my-api.yaml
│   │   └── my-worker/
│   │       └── ...
│   └── staging/
│       └── ...
└── README.md
```

### Using Kustomize

```
my-repo/
├── base/
│   └── my-api/
│       ├── deployment.yaml
│       ├── service.yaml
│       └── kustomization.yaml
└── overlays/
    ├── production/
    │   └── kustomization.yaml
    └── staging/
        └── kustomization.yaml
```

## ArgoCD Setup

### Prerequisites

1. **ArgoCD Installed** - ArgoCD must be installed in your cluster
   ```bash
   # Check if ArgoCD is installed
   kubectl get pods -n argocd
   ```

2. **Git Repository Access** - ArgoCD must have access to your Git repository
   - Public repositories: No configuration needed
   - Private repositories: Configure repository credentials in ArgoCD

3. **ArgoCD Project** - Create or use an existing ArgoCD project
   ```bash
   # List projects
   argocd proj list
   ```

### Configuring Git Repository Access

#### Public Repository

No configuration needed - ArgoCD can access public repositories directly.

#### Private Repository (SSH)

1. **Generate SSH Key:**
   ```bash
   ssh-keygen -t ed25519 -C "argocd" -f argocd-key
   ```

2. **Add Public Key to Git Provider:**
   - GitHub: Settings → SSH and GPG keys
   - GitLab: Settings → SSH Keys
   - Bitbucket: Personal settings → SSH keys

3. **Create ArgoCD Secret:**
   ```bash
   kubectl create secret generic argocd-repo-credentials \
     --from-file=sshPrivateKey=argocd-key \
     -n argocd
   ```

4. **Configure Repository in ArgoCD:**
   ```bash
   argocd repo add git@github.com:org/repo.git \
     --ssh-private-key-path argocd-key
   ```

#### Private Repository (HTTPS with Token)

1. **Create ArgoCD Secret:**
   ```bash
   kubectl create secret generic argocd-repo-credentials \
     --from-literal=username=your-username \
     --from-literal=password=your-token \
     -n argocd
   ```

2. **Configure Repository in ArgoCD:**
   ```bash
   argocd repo add https://github.com/org/repo.git \
     --username your-username \
     --password your-token
   ```

## Best Practices

### 1. Use Environment-Specific Paths

Organize manifests by environment:

```bash
# Production
--git-path manifests/production/my-api

# Staging
--git-path manifests/staging/my-api
```

### 2. Use Semantic Versioning

Tag releases in Git:

```bash
# Deploy specific version
--git-branch v1.2.3

# Or use tags
--git-branch tags/v1.2.3
```

### 3. Enable Auto-Sync for Development

For development environments, enable auto-sync:

```bash
--auto-sync --prune --self-heal
```

### 4. Disable Auto-Sync for Production

For production, use manual sync for better control:

```bash
--no-auto-sync
```

Then sync manually via ArgoCD UI or CLI:

```bash
argocd app sync my-api
```

### 5. Use ArgoCD Projects

Create separate projects for different teams/environments:

```bash
# Create production project
argocd proj create production \
  --description "Production applications" \
  --src https://github.com/org/repo \
  --dest https://kubernetes.default.svc,production

# Use in deployment
--argocd-project production
```

### 6. Write Manifests First

For production deployments, write manifests first:

```bash
# 1. Generate manifests
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --write-manifests ./manifests/my-api

# 2. Review manifests
cat ./manifests/my-api/*.yaml

# 3. Commit to Git
git add manifests/my-api
git commit -m "Add my-api deployment"
git push

# 4. Create ArgoCD Application
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --gitops \
  --git-repo https://github.com/org/repo \
  --git-path manifests/my-api
```

## ArgoCD Application Management

### View Application Status

```bash
# Via kubectl
kubectl get application my-api -n argocd
kubectl describe application my-api -n argocd

# Via ArgoCD CLI
argocd app get my-api
argocd app list
```

### Sync Application

```bash
# Manual sync
argocd app sync my-api

# Sync with prune
argocd app sync my-api --prune

# Sync specific resources
argocd app sync my-api --resource Deployment:my-api
```

### View Application Logs

```bash
# Application events
kubectl get events -n argocd --field-selector involvedObject.name=my-api

# ArgoCD controller logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### Delete Application

```bash
# Delete via kubectl
kubectl delete application my-api -n argocd

# Delete via ArgoCD CLI
argocd app delete my-api
```

## Troubleshooting

### Application Not Syncing

1. **Check Application Status:**
   ```bash
   kubectl get application my-api -n argocd -o yaml
   kubectl describe application my-api -n argocd
   ```

2. **Check Repository Access:**
   ```bash
   # List repositories
   argocd repo list
   
   # Test repository connection
   argocd repo get https://github.com/org/repo
   ```

3. **Check Git Path:**
   ```bash
   # Verify path exists in repository
   git ls-tree -r HEAD --name-only | grep manifests/my-api
   ```

4. **Check ArgoCD Logs:**
   ```bash
   kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
   ```

### Application Out of Sync

1. **Check Sync Status:**
   ```bash
   argocd app get my-api
   ```

2. **View Differences:**
   ```bash
   argocd app diff my-api
   ```

3. **Force Sync:**
   ```bash
   argocd app sync my-api --force
   ```

### Permission Errors

1. **Check ArgoCD Project Permissions:**
   ```bash
   argocd proj get default
   ```

2. **Verify Namespace Access:**
   ```bash
   # Check if project allows namespace
   argocd proj allow-cluster-resource default '*' '*'
   ```

### Repository Authentication Issues

1. **Check Repository Credentials:**
   ```bash
   kubectl get secrets -n argocd | grep repo
   ```

2. **Test Repository Access:**
   ```bash
   argocd repo get https://github.com/org/repo
   ```

3. **Re-add Repository:**
   ```bash
   argocd repo remove https://github.com/org/repo
   argocd repo add https://github.com/org/repo --username user --password token
   ```

## Advanced Configuration

### Custom Sync Options

```yaml
spec:
  syncPolicy:
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
```

### Ignore Differences

Ignore specific fields during sync:

```yaml
spec:
  ignoreDifferences:
  - group: apps
    kind: Deployment
    jsonPointers:
    - /spec/replicas
```

### Multi-Source Applications

For complex applications with multiple sources:

```yaml
spec:
  sources:
  - repoURL: https://github.com/org/app
    path: base
  - repoURL: https://github.com/org/config
    path: config
```

### Helm Support

If using Helm charts:

```yaml
spec:
  source:
    repoURL: https://charts.example.com
    chart: my-chart
    targetRevision: 1.0.0
    helm:
      valueFiles:
      - values.yaml
      parameters:
      - name: image.tag
        value: v1.0.0
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Deploy to ArgoCD

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Generate manifests
      run: |
        mini-idp deploy service my-api \
          --image gcr.io/project/api:${{ github.sha }} \
          --port 8080 \
          --write-manifests ./manifests/my-api
    
    - name: Commit and push
      run: |
        git config user.name "GitHub Actions"
        git config user.email "actions@github.com"
        git add manifests/my-api
        git commit -m "Deploy my-api ${{ github.sha }}" || exit 0
        git push
```

### GitLab CI Example

```yaml
deploy:
  stage: deploy
  script:
    - mini-idp deploy service my-api \
        --image gcr.io/project/api:$CI_COMMIT_SHA \
        --port 8080 \
        --write-manifests ./manifests/my-api
    - git add manifests/my-api
    - git commit -m "Deploy my-api $CI_COMMIT_SHA" || true
    - git push
```

## See Also

- [Kubernetes Components Documentation](k8s-components.md) - ArgoCD setup
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://www.gitops.tech/)

