# Fluent Bit Integration

Mini-IDP automatically integrates with Fluent Bit for centralized log collection and forwarding to GCP Cloud Logging. All deployments are automatically configured for log collection without any additional configuration needed.

## Overview

When you deploy applications using Mini-IDP:

- **Automatic log collection** - Fluent Bit DaemonSet automatically collects logs from all pods
- **Structured metadata** - Logs are tagged with application name, namespace, and environment
- **GCP Cloud Logging** - Logs are automatically forwarded to Google Cloud Logging
- **Zero configuration** - Works out of the box with sensible defaults

## How It Works

### Fluent Bit Architecture

```
┌─────────────────┐
│  Your Pods      │
│  (Applications) │
└────────┬────────┘
         │
         │ Container Logs
         ▼
┌─────────────────┐
│  Fluent Bit     │
│  (DaemonSet)    │
│  - Collects logs│
│  - Parses logs  │
│  - Adds metadata│
└────────┬────────┘
         │
         │ Forwarded Logs
         ▼
┌─────────────────┐
│  GCP Cloud      │
│  Logging        │
└─────────────────┘
```

### Automatic Configuration

Mini-IDP automatically adds the following to your deployments:

1. **Labels** - For log filtering and organization:
   ```yaml
   labels:
     logging: enabled
     logging.app: my-api
     logging.namespace: production
     logging.environment: production  # if specified
   ```

2. **Annotations** - To enable Fluent Bit collection:
   ```yaml
   annotations:
     fluentbit.io/exclude: "false"
   ```

3. **Metadata** - Automatically extracted from pod labels and added to log entries

## Usage

### Basic Usage (Automatic)

Logging is enabled by default for all deployments:

```bash
# Deploy a service - logging automatically enabled
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080

# Logs are automatically collected and forwarded to GCP Cloud Logging
```

### With Environment Label

Add an environment label to organize logs:

```bash
# Deploy with environment label
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --logging-environment production

# Logs will be tagged with logging.environment=production
```

### Disable Logging

Disable log collection for specific deployments:

```bash
# Disable logging for a deployment
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --no-logging
```

## Viewing Logs

### GCP Cloud Logging Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/logs)
2. Select your GCP project
3. Use filters to find your logs:
   ```
   resource.type="k8s_cluster"
   labels."k8s-pod/app"="my-api"
   labels."k8s-pod/namespace"="production"
   ```

### Using gcloud CLI

```bash
# View logs for a specific application
gcloud logging read "resource.type=k8s_cluster AND labels.\"k8s-pod/app\"=my-api" \
  --limit 50 \
  --format json

# View logs with environment filter
gcloud logging read "resource.type=k8s_cluster AND labels.\"k8s-pod/app\"=my-api AND labels.\"k8s-pod/logging.environment\"=production" \
  --limit 50
```

### Using kubectl

```bash
# View logs directly from pods (before Fluent Bit collection)
kubectl logs -l app=my-api -n production --tail=100

# Follow logs
kubectl logs -l app=my-api -n production -f
```

## Log Structure

### Log Entry Format

Logs forwarded to GCP Cloud Logging include:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "severity": "INFO",
  "textPayload": "Application started successfully",
  "resource": {
    "type": "k8s_cluster",
    "labels": {
      "cluster_name": "my-cluster",
      "location": "us-central1",
      "namespace_name": "production",
      "pod_name": "my-api-7d4f8b9c6-abc123",
      "container_name": "my-api"
    }
  },
  "labels": {
    "k8s-pod/app": "my-api",
    "k8s-pod/namespace": "production",
    "k8s-pod/logging.environment": "production",
    "k8s-pod/logging": "enabled"
  }
}
```

### Log Fields

- **timestamp**: Log entry timestamp
- **severity**: Log level (INFO, WARN, ERROR, etc.)
- **textPayload**: Log message content
- **resource.labels**: Kubernetes resource information
- **labels**: Custom labels for filtering

## Configuration

### Fluent Bit Setup

Fluent Bit is automatically deployed as part of the infrastructure setup. See [Kubernetes Components Documentation](k8s-components.md) for details.

### Workload Identity

Fluent Bit uses Workload Identity to authenticate with GCP Cloud Logging. The service account is automatically configured during infrastructure deployment.

### Custom Log Parsing

To customize log parsing, you can:

1. **Modify Fluent Bit configuration** in `infrastructure/k8s_components.py`
2. **Add custom parsers** for specific log formats
3. **Configure filters** for log transformation

Example custom parser configuration:

```python
"parsers": {
    "parsers.conf": """
[PARSER]
    Name myapp
    Format regex
    Regex ^(?<timestamp>\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}) \\[(?<level>\\w+)\\] (?<message>.*)$
    Time_Key timestamp
    Time_Format %Y-%m-%d %H:%M:%S
"""
}
```

## Best Practices

### 1. Use Environment Labels

Always specify `--logging-environment` to organize logs:

```bash
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --logging-environment production
```

### 2. Structured Logging

Use structured logging in your applications:

```python
import json
import logging

logger = logging.getLogger(__name__)

# Structured log entry
logger.info(json.dumps({
    "event": "user_login",
    "user_id": "12345",
    "ip_address": "192.168.1.1"
}))
```

### 3. Log Levels

Use appropriate log levels:
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARN**: Warning messages
- **ERROR**: Error conditions
- **FATAL**: Critical errors

### 4. Sensitive Data

Never log sensitive information:
- Passwords
- API keys
- Personal identifiable information (PII)
- Credit card numbers

### 5. Log Retention

Configure log retention in GCP Cloud Logging:
- Default: 30 days
- Can be extended up to 365 days
- Consider exporting important logs to BigQuery for long-term storage

## Troubleshooting

### Logs Not Appearing in Cloud Logging

1. **Check Fluent Bit is running:**
   ```bash
   kubectl get pods -n logging -l app.kubernetes.io/name=fluent-bit
   ```

2. **Check Fluent Bit logs:**
   ```bash
   kubectl logs -n logging -l app.kubernetes.io/name=fluent-bit --tail=100
   ```

3. **Verify Workload Identity:**
   ```bash
   kubectl get serviceaccount fluent-bit -n logging -o yaml | grep annotations
   ```

4. **Check pod labels:**
   ```bash
   kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A 10 labels
   ```

### Fluent Bit Errors

Common errors and solutions:

- **Permission denied**: Check Workload Identity binding
- **Connection refused**: Verify GCP Logging API is enabled
- **No logs collected**: Check pod labels include `logging: enabled`

### Viewing Fluent Bit Configuration

```bash
# View Fluent Bit configmap
kubectl get configmap -n logging fluent-bit -o yaml

# View Fluent Bit service account
kubectl get serviceaccount fluent-bit -n logging -o yaml
```

## Advanced Configuration

### Custom Log Filters

Add custom filters in Fluent Bit configuration:

```python
"filters": {
    "filters.conf": """
[FILTER]
    Name grep
    Match my-api.*
    Exclude level DEBUG
"""
}
```

### Multiple Outputs

Configure multiple log outputs (e.g., Cloud Logging + BigQuery):

```python
"outputs": {
    "outputs.conf": """
[OUTPUT]
    Name stackdriver
    Match *
    resource k8s_cluster
    ...

[OUTPUT]
    Name bigquery
    Match production.*
    project_id my-project
    dataset logs
    table app_logs
"""
}
```

### Log Sampling

Reduce log volume with sampling:

```python
"filters": {
    "filters.conf": """
[FILTER]
    Name throttle
    Match *
    Rate 100
"""
}
```

## Integration with Other Tools

### Prometheus

Logs can be correlated with metrics using labels:
- Use `logging.app` label to match with Prometheus metrics
- Combine log analysis with metric analysis

### Grafana

Import GCP Cloud Logging as a data source in Grafana:
1. Add Cloud Logging data source
2. Create dashboards with log queries
3. Correlate logs with metrics

### Alerting

Set up alerts based on log patterns:
- Error rate thresholds
- Specific error messages
- Log volume anomalies

## See Also

- [Kubernetes Components Documentation](k8s-components.md) - Fluent Bit setup
- [GCP Cloud Logging Documentation](https://cloud.google.com/logging/docs)
- [Fluent Bit Documentation](https://docs.fluentbit.io/)

