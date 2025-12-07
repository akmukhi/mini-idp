# Automatic HPA Generation

Mini-IDP automatically generates HorizontalPodAutoscaler (HPA) resources with sensible defaults based on your deployment type and configuration. This eliminates the need to manually configure HPA settings while ensuring optimal scaling behavior.

## Overview

When you deploy a service or worker with autoscaling enabled (default), Mini-IDP automatically:

- Calculates appropriate min/max replica ranges
- Sets type-specific CPU targets
- Configures scaling behavior policies
- Generates HPA resources alongside your deployment

## Automatic Defaults

### Min/Max Replicas Calculation

The system automatically calculates min and max replicas based on:

1. **Initial replica count** - The `--replicas` value you specify
2. **Deployment type** - Service vs Worker have different scaling strategies
3. **User overrides** - You can override any calculated value

#### Min Replicas Logic

- If `replicas = 1`: `min_replicas = 1`
- If `replicas > 1`: `min_replicas = max(1, replicas // 2)`
  - This allows for rolling updates without downtime
  - Example: 5 replicas → min = 2 (allows 3 pods to be updated while 2 remain)

#### Max Replicas Logic

- **Services**: `max_replicas = max(10, replicas * 3)`
  - 3x multiplier for burst capacity
  - Minimum of 10 replicas
- **Workers**: `max_replicas = max(10, replicas * 2)`
  - 2x multiplier for queue processing
  - Minimum of 10 replicas

#### Examples

| Type | Replicas | Calculated Min | Calculated Max | Reason |
|------|----------|----------------|----------------|--------|
| Service | 1 | 1 | 10 | Minimum max is 10 |
| Service | 3 | 1 | 10 | 3×3=9, but min max is 10 |
| Service | 5 | 2 | 15 | 5×3=15 |
| Service | 10 | 5 | 30 | 10×3=30 |
| Worker | 3 | 1 | 10 | 3×2=6, but min max is 10 |
| Worker | 5 | 2 | 10 | 5×2=10 |
| Worker | 10 | 5 | 20 | 10×2=20 |

### CPU Target Defaults

CPU utilization targets are set automatically based on deployment type:

- **Services**: 70% CPU target
  - Balanced scaling for web applications and APIs
  - Allows headroom for traffic spikes
- **Workers**: 60% CPU target
  - More aggressive scaling for queue processing
  - Ensures workers scale up faster when queues build up

### Memory Target

- Default: 80% memory utilization
- Can be customized with `--memory-target`
- Only included if explicitly set

## HPA Behavior Configuration

The generated HPA includes optimized scaling behavior policies:

### Scale Down Behavior

- **Stabilization Window**: 300 seconds (5 minutes)
  - Prevents rapid scale-down after temporary load spikes
- **Policy**: 50% reduction per 60 seconds
  - Gradual scale-down to avoid over-reacting

### Scale Up Behavior

- **Stabilization Window**: 0 seconds (immediate)
  - Allows rapid response to increased load
- **Policies** (selects the more aggressive):
  - **Percent-based**: 100% increase per 15 seconds
  - **Pods-based**: 4 pods per 15 seconds
- **SelectPolicy**: Max (uses the more aggressive policy)

This configuration ensures:
- Fast scale-up when load increases
- Gradual scale-down to prevent thrashing
- Stable operation during normal conditions

## Usage

### Basic Usage (Automatic Defaults)

```bash
# Deploy a service - HPA automatically configured
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --replicas 3

# Automatically generates:
# - min_replicas: 1
# - max_replicas: 10
# - cpu_target: 70%
```

### Worker Deployment

```bash
# Deploy a worker - different defaults
mini-idp deploy worker queue-processor \
  --image gcr.io/project/worker:latest \
  --replicas 5

# Automatically generates:
# - min_replicas: 2
# - max_replicas: 10
# - cpu_target: 60%
```

### Override Automatic Defaults

You can override any calculated value:

```bash
# Override min/max replicas
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --replicas 3 \
  --min-replicas 2 \
  --max-replicas 20

# Override CPU target
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --replicas 3 \
  --cpu-target 80

# Override memory target
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --replicas 3 \
  --memory-target 75
```

### Disable Autoscaling

```bash
# Disable HPA generation
mini-idp deploy service my-api \
  --image gcr.io/project/api:v1.0 \
  --port 8080 \
  --no-autoscaling
```

## Generated HPA Resource

The automatically generated HPA resource includes:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-api
  namespace: default
  labels:
    app: my-api
    managed-by: mini-idp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-api
  minReplicas: 1
  maxReplicas: 10
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Best Practices

### When to Use Automatic Defaults

Automatic defaults work well for:
- Standard web applications and APIs
- Queue processing workers
- Most stateless workloads
- Development and staging environments

### When to Override Defaults

Consider overriding defaults for:
- **High-traffic services**: Increase max_replicas
- **Cost-sensitive workloads**: Lower max_replicas, increase CPU target
- **Latency-sensitive applications**: Lower CPU target (e.g., 50%)
- **Batch workers**: May need different scaling strategies

### Recommendations

1. **Start with automatic defaults** - They work well for most cases
2. **Monitor and adjust** - Use metrics to fine-tune if needed
3. **Set resource requests/limits** - HPA needs resource metrics to work
4. **Consider memory targets** - Add `--memory-target` for memory-bound workloads

## Troubleshooting

### HPA Not Scaling

- **Check resource requests**: HPA requires CPU/memory requests to be set
- **Verify metrics**: Ensure metrics-server is installed
- **Check current utilization**: `kubectl top pods`

### Scaling Too Aggressively

- Increase CPU target (e.g., `--cpu-target 80`)
- Adjust scale-up policies in the template
- Increase stabilization windows

### Scaling Too Slowly

- Decrease CPU target (e.g., `--cpu-target 60`)
- Check if metrics are being collected
- Verify HPA status: `kubectl describe hpa <name>`

## Advanced Configuration

### Custom HPA Behavior

To customize HPA behavior periods, you can:

1. Create a custom template based on `service.yaml.j2` or `worker.yaml.j2`
2. Modify the `behavior` section in the template
3. Use `--template` flag to use your custom template

### Multiple Metrics

The current implementation supports:
- CPU utilization (automatic)
- Memory utilization (optional, via `--memory-target`)

For custom metrics (e.g., queue length), you can:
1. Create a custom template
2. Add external metrics to the HPA spec
3. Use the template with `--template` flag

## See Also

- [Deploy Command Documentation](../README.md#deploy-command)
- [Template System Documentation](templates/README.md)
- [Kubernetes HPA Documentation](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

