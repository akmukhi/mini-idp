# Security and GitIgnore Guide

This document outlines which files should **NOT** be committed to GitHub to protect sensitive information.

## Critical Files to Never Commit

### 1. Pulumi Stack Files (HIGH PRIORITY)

**Files to ignore:**
- `Pulumi.*.yaml` (all stack-specific files)
- `Pulumi.*.json`
- `.pulumi/` directory

**Why:** These files contain:
- GCP project IDs
- Configuration values
- Potentially encrypted secrets
- Stack state information

**Example files:**
```
infrastructure/Pulumi.mini-idp-test.yaml  ❌ DO NOT COMMIT
infrastructure/Pulumi.dev.yaml             ❌ DO NOT COMMIT
infrastructure/Pulumi.prod.yaml            ❌ DO NOT COMMIT
.pulumi/stacks/                            ❌ DO NOT COMMIT
```

**Safe to commit:**
- `Pulumi.yaml` (project configuration, no secrets) ✅

### 2. Service Account Keys and Credentials

**Files to ignore:**
- `*-key.json`
- `service-account*.json`
- `gcp-key*.json`
- `*credentials.json`
- `*.pem`
- `*.key`
- `*.p12`
- `*.pfx`

**Why:** These contain authentication credentials that provide access to your GCP resources.

### 3. Environment Files

**Files to ignore:**
- `.env`
- `.env.local`
- `.env.*.local`
- `*.env`

**Why:** May contain API keys, passwords, and other sensitive configuration.

### 4. Kubernetes Configuration

**Files to ignore:**
- `kubeconfig`
- `kubeconfig.*`
- `*.kubeconfig`

**Why:** Contains cluster authentication tokens and certificates.

### 5. Test Configuration Files

**Files to ignore:**
- `testconfig.py` (if it contains real project IDs or secrets)
- `*test*.yaml` (if they contain sensitive config)

**Why:** May contain real project IDs or test credentials.

### 6. Secrets Directories

**Files to ignore:**
- `secrets/`
- `.secrets/`
- Any directory containing secrets

## Files Safe to Commit

These files are **safe** to commit:

✅ **Code files:**
- `*.py` (Python source code)
- `*.md` (Documentation)
- `*.sh` (Shell scripts)

✅ **Configuration templates:**
- `Pulumi.yaml` (project config, no secrets)
- `requirements.txt`
- `pyproject.toml`
- `.flake8`

✅ **Infrastructure code:**
- `__main__.py`
- `config.py` (helper functions, no actual secrets)
- `k8s_components.py`
- `k8s_config.py`

✅ **Documentation:**
- `docs/*.md`
- `README.md`

## Current Files Status

Based on your repository, here are files that should be checked:

### ⚠️ Files to Review Before Committing:

1. **`infrastructure/Pulumi.mini-idp-test.yaml`**
   - Contains: `gcp:project: test-mini-idp`
   - **Action:** Should be in `.gitignore` (already added)
   - **Status:** Contains project ID - should not commit

2. **`infrastructure/testconfig.py`**
   - **Action:** Review contents - if it has real project IDs, don't commit
   - **Status:** Check if it contains sensitive data

### ✅ Files Safe to Commit:

- `infrastructure/__main__.py`
- `infrastructure/config.py`
- `infrastructure/k8s_components.py`
- `infrastructure/k8s_config.py`
- `infrastructure/Pulumi.yaml`
- `infrastructure/requirements.txt`
- `infrastructure/README.md`
- All files in `docs/`
- `.gitignore` (the file itself)

## How to Check What Will Be Committed

Before pushing, always check what files Git will include:

```bash
# See what files are staged
git status

# See what will be committed
git diff --cached

# Check if sensitive files are tracked
git ls-files | grep -E "(Pulumi\.|\.env|\.key|\.json|secret)"

# Verify .gitignore is working
git status --ignored
```

## Best Practices

### 1. Use Environment Variables or Pulumi Config

Instead of hardcoding secrets in files:

```python
# ❌ BAD - Don't do this
project_id = "my-project-123"

# ✅ GOOD - Use Pulumi config
project_id = pulumi.Config("gcp").require("project")
```

### 2. Use Pulumi Secrets

For sensitive values, use Pulumi's secret management:

```bash
# Set a secret (encrypted in stack file)
pulumi config set --secret database:password mypassword

# This will be encrypted in Pulumi.*.yaml files
# But still, don't commit those files!
```

### 3. Use .gitignore

The `.gitignore` file has been created with common patterns. Always review it before committing.

### 4. Review Before Committing

```bash
# Always review what you're about to commit
git diff

# Check for sensitive patterns
git diff | grep -iE "(password|secret|key|token|credential)"
```

### 5. Use GitHub Secrets for CI/CD

If using GitHub Actions:
- Store secrets in GitHub Secrets (Settings → Secrets)
- Never hardcode secrets in workflow files

## If You Accidentally Committed Sensitive Data

If you've already committed sensitive information:

1. **Immediately rotate/revoke the exposed credentials:**
   - Rotate GCP service account keys
   - Change passwords
   - Revoke API keys

2. **Remove from Git history:**
   ```bash
   # Remove file from history (use with caution)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch PATH_TO_FILE" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (warn collaborators first!)
   git push origin --force --all
   ```

3. **Consider using git-secrets or git-crypt** for future protection

## Verification Checklist

Before pushing to GitHub, verify:

- [ ] No `Pulumi.*.yaml` files are staged (except `Pulumi.yaml`)
- [ ] No `.env` files are staged
- [ ] No `*.json` credential files are staged
- [ ] No `kubeconfig` files are staged
- [ ] No hardcoded passwords or API keys in code
- [ ] `.gitignore` is up to date
- [ ] Reviewed `git status` output
- [ ] Checked for sensitive patterns in diffs

## Additional Resources

- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Pulumi: Secrets Management](https://www.pulumi.com/docs/intro/concepts/secrets/)
- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

