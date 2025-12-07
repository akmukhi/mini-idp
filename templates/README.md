# Kubernetes Templates

Jinja2 templates for generating Kubernetes resources for services, jobs, and workers.

## Available Templates

- **`service.yaml.j2`** - For stateless services (web apps, APIs)
- **`job.yaml.j2`** - For one-time or scheduled jobs
- **`worker.yaml.j2`** - For long-running worker processes

## Template Variables

### Common Variables

All templates support these common variables:

- `name` (required) - Application name
- `namespace` (default: "default") - Kubernetes namespace
- `image` (required) - Container image
- `labels` (optional) - Additional labels to apply
- `env_vars` (optional) - Environment variables (list of dicts with `name` and `value`)
- `resources` (optional) - Resource requests/limits

### Service Template

```yaml
name: my-service
namespace: production
image: gcr.io/project/app:v1.0.0
port: 8080
replicas: 3
service_type: LoadBalancer
autoscaling: true
min_replicas: 2
max_replicas: 10
cpu_target: 70
memory_target: 80
metrics: true
metrics_path: /metrics
metrics_interval: 30s
liveness_probe:
  path: /health
  port: 8080
  initial_delay: 30
readiness_probe:
  path: /ready
  port: 8080
  initial_delay: 5
```

### Job Template

```yaml
name: data-processor
namespace: default
image: gcr.io/project/processor:latest
job_type: Job  # or "CronJob"
schedule: "0 9 * * *"  # Required for CronJob
command: ["python", "process.py"]
args: ["--input", "data.csv"]
completions: 1
parallelism: 1
backoff_limit: 3
restart_policy: Never
```

### Worker Template

```yaml
name: queue-worker
namespace: default
image: gcr.io/project/worker:latest
replicas: 3
strategy: RollingUpdate
autoscaling: true
min_replicas: 2
max_replicas: 20
cpu_target: 70
memory_target: 80
metrics: true
queue_length_metric:
  name: queue_length
  target: "5"
```

## Usage

### Using TemplateManager

```python
from lib.template_manager import TemplateManager

manager = TemplateManager()

# List available templates
templates = manager.list_templates()
print(templates)  # ['job', 'service', 'worker']

# Render a template
context = {
    "name": "my-app",
    "namespace": "default",
    "image": "nginx:latest",
    "port": 80,
    "replicas": 2,
}
resources = manager.render_to_resources("service", context)
```

### Using TemplateBuilder

```python
from lib.template_builder import TemplateBuilder

builder = TemplateBuilder()

# Build a service
resources = builder.build_service(
    name="my-api",
    image="gcr.io/project/api:v1.0",
    namespace="production",
    port=8080,
    replicas=3,
    env_vars=[{"name": "ENV", "value": "production"}],
    autoscaling=True,
    min_replicas=2,
    max_replicas=10,
)

# Build a job
resources = builder.build_job(
    name="data-processor",
    image="gcr.io/project/processor:latest",
    command=["python", "process.py"],
    args=["--input", "data.csv"],
)

# Build a worker
resources = builder.build_worker(
    name="queue-worker",
    image="gcr.io/project/worker:latest",
    replicas=3,
    autoscaling=True,
)
```

## Template Structure

Templates generate multiple Kubernetes resources separated by `---`:

1. **Deployment/Job/CronJob** - Main workload
2. **Service** - (Service/Worker templates only) Exposes the deployment
3. **HorizontalPodAutoscaler** - (If autoscaling enabled) Scales based on metrics with intelligent defaults
4. **ServiceMonitor** - (If metrics enabled) Prometheus metrics collection
5. **ExternalSecret** - (If external secrets specified) Syncs secrets from GCP Secret Manager

## New Features

### Automatic HPA Generation

Templates automatically generate HPA resources with intelligent defaults:

- **Services**: 70% CPU target, 3x max replicas multiplier
- **Workers**: 60% CPU target, 2x max replicas multiplier
- **Min Replicas**: Automatically calculated as 50% of initial replicas (minimum 1)
- **Scaling Behavior**: Configured with scale-up and scale-down policies

### Fluent Bit Logging

All templates include automatic log collection:

- Logs automatically collected by Fluent Bit
- Forwarded to GCP Cloud Logging
- Tagged with app name, namespace, and environment
- Enabled by default

### Prometheus Metrics

Templates support automatic metrics collection:

- ServiceMonitor resources generated automatically
- Configurable metrics path, port, and interval
- Standard Prometheus annotations added to pods

### External Secrets

Templates support external secret injection:

- ExternalSecret resources generated automatically
- Syncs from GCP Secret Manager
- Automatic secret refresh at configured intervals

## Customization

You can create custom templates by:

1. Adding a new `.yaml.j2` file to the `templates/` directory
2. Using the same variable structure
3. Loading it with `TemplateManager.load_template()`

## Environment Variables

Environment variables can be provided in two formats:

1. **Dictionary format** (for programmatic use):
   ```python
   env_vars = [
       {"name": "KEY", "value": "value"},
       {"name": "SECRET_KEY", "secret": "my-secret", "key": "secret-key"},
   ]
   ```

2. **CLI format** (for command-line use):
   ```bash
   --env KEY=value
   --secret my-secret:secret-key
   ```

## Examples

See `lib/examples.py` for complete usage examples.

