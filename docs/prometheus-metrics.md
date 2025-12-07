# Prometheus Metrics Integration

Mini-IDP automatically generates Prometheus ServiceMonitor resources for metrics collection. All deployments can expose metrics that are automatically discovered and scraped by Prometheus.

## Overview

When you deploy applications with metrics enabled (default), Mini-IDP automatically:

- **Generates ServiceMonitor** - Prometheus custom resource for metrics discovery
- **Configures scrape endpoints** - Sets up metrics path, port, and interval
- **Adds Prometheus annotations** - Standard annotations for pod discovery
- **Zero configuration** - Works out of the box with sensible defaults

## How It Works

### Prometheus Architecture

```
┌─────────────────┐
│  Your Pods      │
│  (Applications) │
│  /metrics       │
└────────┬────────┘
         │
         │ HTTP GET /metrics
         ▼
┌─────────────────┐
│  Prometheus     │
│  (via           │
│  ServiceMonitor)│
└────────┬────────┘
         │
         │ Scraped Metrics
         ▼
┌─────────────────┐
│  Grafana        │
│  (Visualization)│
└─────────────────┘
```

### Automatic Configuration

Mini-IDP automatically adds:

1. **ServiceMonitor Resource** - Custom resource that tells Prometheus what to scrape:
   ```yaml
   apiVersion: monitoring.coreos.com/v1
   kind: ServiceMonitor
   metadata:
     name: my-api
     namespace: production
   spec:
     selector:
       matchLabels:
         app: my-api
     endpoints:
     - port: http
       path: /metrics
       interval: 30s
   ```

2. **Prometheus Annotations** - Standard annotations on pods:
   ```yaml
   annotations:
     prometheus.io/scrape: "true"
     prometheus.io/port: "8080"
     prometheus.io/path: "/metrics"
   ```

3. **Service Port** - Service port is named to match metrics port for ServiceMonitor

## Usage

### Basic Usage (Automatic)

Metrics are enabled by default for all deployments:

```bash
# Deploy a service - ServiceMonitor automatically generated
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080

# ServiceMonitor is automatically created with:
# - Port: http (matches service port)
# - Path: /metrics
# - Interval: 30s
```

### Custom Metrics Path

```bash
# Use custom metrics path
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --metrics-path /api/metrics
```

### Custom Metrics Port

```bash
# Use custom metrics port name
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --metrics-port metrics
```

### Custom Scrape Interval

```bash
# Change scrape interval
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --metrics-interval 15s
```

### Disable Metrics

```bash
# Disable metrics collection
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --no-metrics
```

## Metrics Endpoint Requirements

### Standard Prometheus Format

Your application should expose metrics in Prometheus format:

```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1234
http_requests_total{method="POST",status="200"} 567
http_requests_total{method="GET",status="404"} 12

# HELP http_request_duration_seconds Request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 1000
http_request_duration_seconds_bucket{le="0.5"} 1500
http_request_duration_seconds_bucket{le="1.0"} 1800
```

### Common Metrics Libraries

#### Python (Prometheus Client)

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
http_requests = Counter('http_requests_total', 'Total HTTP requests', ['method', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'Request duration')

# Expose metrics endpoint
start_http_server(8080)  # Or use /metrics endpoint in your web framework
```

#### Node.js (prom-client)

```javascript
const promClient = require('prom-client');

// Create metrics registry
const register = new promClient.Registry();

// Define metrics
const httpRequests = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'status']
});

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.end(await register.metrics());
});
```

#### Go (prometheus/client_golang)

```go
import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

// Define metrics
var httpRequests = prometheus.NewCounterVec(
    prometheus.CounterOpts{
        Name: "http_requests_total",
        Help: "Total HTTP requests",
    },
    []string{"method", "status"},
)

// Register metrics
prometheus.MustRegister(httpRequests)

// Expose metrics endpoint
http.Handle("/metrics", promhttp.Handler())
```

## ServiceMonitor Configuration

### Default Values

- **Port**: `http` (matches service port name)
- **Path**: `/metrics`
- **Interval**: `30s`

### Advanced Configuration

You can customize ServiceMonitor through template variables:

```python
# In your code
resources = builder.build_service(
    name="my-api",
    image="gcr.io/project/api:v1.0",
    port=8080,
    metrics=True,
    metrics_path="/api/v1/metrics",
    metrics_port="metrics",
    metrics_interval="15s",
    metrics_labels={"team": "backend", "tier": "api"},
)
```

### TLS Configuration

For HTTPS metrics endpoints:

```python
resources = builder.build_service(
    name="my-api",
    image="gcr.io/project/api:v1.0",
    port=8080,
    metrics=True,
    metrics_scheme="https",
    metrics_tls_config={"insecureSkipVerify": False},
)
```

## Viewing Metrics

### Prometheus UI

1. Port-forward to Prometheus:
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
   ```

2. Open http://localhost:9090

3. Query metrics:
   ```
   http_requests_total
   rate(http_requests_total[5m])
   http_request_duration_seconds{quantile="0.95"}
   ```

### Grafana

1. Access Grafana (see [Kubernetes Components Guide](k8s-components.md))

2. Create dashboards using Prometheus data source

3. Use pre-built dashboards:
   - Kubernetes Pods
   - Node Exporter
   - Application-specific dashboards

### Using PromQL

Common Prometheus queries:

```promql
# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# P95 latency
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# CPU usage
rate(container_cpu_usage_seconds_total[5m])

# Memory usage
container_memory_usage_bytes
```

## Best Practices

### 1. Use Standard Metrics

Follow Prometheus naming conventions:
- Use `_total` suffix for counters
- Use `_seconds` suffix for durations
- Use `_bytes` suffix for byte values
- Use `_bucket` suffix for histogram buckets

### 2. Add Labels Wisely

Labels add dimensionality but increase cardinality:
- ✅ Good: `method`, `status`, `endpoint`
- ❌ Bad: `user_id`, `request_id`, `timestamp`

### 3. Expose Business Metrics

Beyond infrastructure metrics, expose business metrics:
- User signups
- Orders processed
- API calls by feature
- Error rates by component

### 4. Set Appropriate Intervals

- **High-frequency services**: 15s interval
- **Standard services**: 30s interval (default)
- **Low-frequency services**: 60s interval

### 5. Monitor Cardinality

High cardinality can cause performance issues:
```bash
# Check metric cardinality in Prometheus
prometheus_tsdb_head_series
```

## Troubleshooting

### Metrics Not Appearing in Prometheus

1. **Check ServiceMonitor exists:**
   ```bash
   kubectl get servicemonitor -n <namespace>
   kubectl describe servicemonitor <name> -n <namespace>
   ```

2. **Verify Prometheus is discovering targets:**
   ```bash
   # Port-forward to Prometheus
   kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
   
   # Check targets at http://localhost:9090/targets
   ```

3. **Check pod annotations:**
   ```bash
   kubectl get pod <pod-name> -n <namespace> -o yaml | grep prometheus.io
   ```

4. **Verify metrics endpoint:**
   ```bash
   # Port-forward to pod
   kubectl port-forward <pod-name> 8080:8080 -n <namespace>
   
   # Test metrics endpoint
   curl http://localhost:8080/metrics
   ```

### ServiceMonitor Not Created

- Verify `--metrics` flag is set (default: enabled)
- Check template includes ServiceMonitor section
- Verify Prometheus Operator is installed

### High Cardinality Issues

- Reduce number of label values
- Use recording rules to aggregate metrics
- Consider using exemplars for detailed tracing

## Advanced Configuration

### Multiple Endpoints

For applications exposing multiple metric endpoints:

```python
# Custom template with multiple endpoints
servicemonitor = {
    "spec": {
        "endpoints": [
            {
                "port": "http",
                "path": "/metrics",
                "interval": "30s",
            },
            {
                "port": "http",
                "path": "/custom-metrics",
                "interval": "60s",
            },
        ],
    },
}
```

### Relabeling

Configure metric relabeling in ServiceMonitor:

```yaml
spec:
  endpoints:
  - port: http
    path: /metrics
    relabelings:
    - sourceLabels: [__meta_kubernetes_pod_name]
      targetLabel: pod_name
```

### ServiceMonitor Selector

Customize ServiceMonitor selector:

```yaml
spec:
  selector:
    matchLabels:
      app: my-api
      metrics: enabled
  namespaceSelector:
    matchNames:
    - production
    - staging
```

## Integration with Other Tools

### Grafana Dashboards

Import pre-built dashboards:
- Kubernetes Pods Dashboard
- Node Exporter Dashboard
- Application-specific dashboards

### Alerting

Set up Prometheus alerts based on metrics:
- High error rates
- Latency thresholds
- Resource usage

### Recording Rules

Create recording rules for aggregated metrics:
```yaml
groups:
- name: my_api
  interval: 30s
  rules:
  - record: my_api:http_requests:rate5m
    expr: rate(http_requests_total[5m])
```

## See Also

- [Kubernetes Components Documentation](k8s-components.md) - Prometheus setup
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Prometheus Client Libraries](https://prometheus.io/docs/instrumenting/clientlibs/)
- [ServiceMonitor CRD](https://github.com/prometheus-operator/prometheus-operator/blob/main/Documentation/api.md#servicemonitor)

