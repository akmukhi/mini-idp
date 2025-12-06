"""
Kubernetes infrastructure components deployment.
Deploys ArgoCD, Prometheus+Grafana, Fluent Bit, External Secrets Operator,
and cert-manager using Helm charts via Pulumi.
"""

import pulumi
import pulumi_kubernetes as k8s
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts

from config import get_gcp_project, get_gcp_region, get_cluster_name
from k8s_config import (
    get_argocd_config,
    get_prometheus_config,
    get_fluentbit_config,
    get_external_secrets_config,
    get_certmanager_config,
)

# Get configuration
project = get_gcp_project()
region = get_gcp_region()
cluster_name = get_cluster_name()

# Get component configurations
argocd_config = get_argocd_config()
prometheus_config = get_prometheus_config()
fluentbit_config = get_fluentbit_config()
external_secrets_config = get_external_secrets_config()
certmanager_config = get_certmanager_config()

# Provider configuration - will use kubeconfig from environment
k8s_provider = k8s.Provider(
    "k8s-provider",
    kubeconfig=None,  # Will use default kubeconfig
)

# ============================================================================
# 1. cert-manager (deploy first - needed for TLS)
# ============================================================================
cert_manager_namespace = k8s.core.v1.Namespace(
    "cert-manager-ns",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=certmanager_config["namespace"],
        labels={"app": "cert-manager"},
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

cert_manager = Chart(
    "cert-manager",
    ChartOpts(
        chart="cert-manager",
        version=certmanager_config["chart_version"],
        namespace=certmanager_config["namespace"],
        fetch_opts=FetchOpts(
            repo="https://charts.jetstack.io",
        ),
        values={
            "installCRDs": True,
            "global": {
                "podSecurityPolicy": {
                    "enabled": False,
                },
            },
            "prometheus": {
                "enabled": True,
            },
        },
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[cert_manager_namespace],
    ),
)

# ClusterIssuer for Let's Encrypt (if email provided)
if certmanager_config["letsencrypt_email"]:
    letsencrypt_issuer = k8s.apiextensions.CustomResource(
        "letsencrypt-issuer",
        api_version="cert-manager.io/v1",
        kind="ClusterIssuer",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="letsencrypt-prod",
        ),
        spec={
            "acme": {
                "server": certmanager_config["letsencrypt_server"],
                "email": certmanager_config["letsencrypt_email"],
                "privateKeySecretRef": {
                    "name": "letsencrypt-prod",
                },
                "solvers": [
                    {
                        "http01": {
                            "ingress": {
                                "class": "nginx",
                            },
                        },
                    },
                ],
            },
        },
        opts=pulumi.ResourceOptions(
            provider=k8s_provider,
            depends_on=[cert_manager],
        ),
    )

# ============================================================================
# 2. External Secrets Operator
# ============================================================================
external_secrets_namespace = k8s.core.v1.Namespace(
    "external-secrets-ns",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=external_secrets_config["namespace"],
        labels={"app": "external-secrets"},
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

external_secrets = Chart(
    "external-secrets",
    ChartOpts(
        chart="external-secrets",
        version=external_secrets_config["chart_version"],
        namespace=external_secrets_config["namespace"],
        fetch_opts=FetchOpts(
            repo="https://charts.external-secrets.io",
        ),
        values={
            "installCRDs": True,
            "serviceAccount": {
                "annotations": {
                    "iam.gke.io/gcp-service-account": (
                        f"external-secrets@{project}.iam.gserviceaccount.com"
                    ),
                },
            },
        },
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[external_secrets_namespace],
    ),
)

# ============================================================================
# 3. Prometheus + Grafana Stack
# ============================================================================
monitoring_namespace = k8s.core.v1.Namespace(
    "monitoring-ns",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=prometheus_config["namespace"],
        labels={"app": "monitoring"},
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

prometheus_stack = Chart(
    "kube-prometheus-stack",
    ChartOpts(
        chart="kube-prometheus-stack",
        version=prometheus_config["chart_version"],
        namespace=prometheus_config["namespace"],
        fetch_opts=FetchOpts(
            repo="https://prometheus-community.github.io/helm-charts",
        ),
        values={
            "grafana": {
                "adminPassword": prometheus_config["grafana_admin_password"],
                "persistence": {
                    "enabled": True,
                    "storageClassName": prometheus_config["storage_class"],
                },
                "service": {
                    "type": "LoadBalancer",
                },
            },
            "prometheus": {
                "prometheusSpec": {
                    "retention": prometheus_config["prometheus_retention"],
                    "storageSpec": {
                        "volumeClaimTemplate": {
                            "spec": {
                                "storageClassName": prometheus_config["storage_class"],
                                "accessModes": ["ReadWriteOnce"],
                                "resources": {
                                    "requests": {
                                        "storage": "50Gi",
                                    },
                                },
                            },
                        },
                    },
                },
                "service": {
                    "type": "LoadBalancer",
                },
            },
            "alertmanager": {
                "alertmanagerSpec": {
                    "storage": {
                        "volumeClaimTemplate": {
                            "spec": {
                                "storageClassName": prometheus_config["storage_class"],
                                "accessModes": ["ReadWriteOnce"],
                                "resources": {
                                    "requests": {
                                        "storage": "10Gi",
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[monitoring_namespace],
    ),
)

# ============================================================================
# 4. Fluent Bit
# ============================================================================
logging_namespace = k8s.core.v1.Namespace(
    "logging-ns",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=fluentbit_config["namespace"],
        labels={"app": "logging"},
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

fluent_bit = Chart(
    "fluent-bit",
    ChartOpts(
        chart="fluent-bit",
        version=fluentbit_config["chart_version"],
        namespace=fluentbit_config["namespace"],
        fetch_opts=FetchOpts(
            repo="https://fluent.github.io/helm-charts",
        ),
        values={
            "config": {
                "service": {
                    "parsers": {
                        "parsers.conf": """
[PARSER]
    Name docker
    Format json
    Time_Key time
    Time_Format %Y-%m-%dT%H:%M:%S.%L
    Time_Keep On
""",
                    },
                },
                "outputs": {
                    "outputs.conf": f"""
[OUTPUT]
    Name stackdriver
    Match *
    resource k8s_cluster
    k8s_cluster_name {cluster_name}
    k8s_cluster_location {region}
    google_service_credentials /var/secrets/google/key.json
""",
                },
            },
            "serviceAccount": {
                "annotations": {
                    "iam.gke.io/gcp-service-account": (
                        f"fluent-bit@{project}.iam.gserviceaccount.com"
                    ),
                },
            },
        },
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[logging_namespace],
    ),
)

# ============================================================================
# 5. ArgoCD
# ============================================================================
argocd_namespace = k8s.core.v1.Namespace(
    "argocd-ns",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name=argocd_config["namespace"],
        labels={"app": "argocd"},
    ),
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

argocd_values: dict = {
    "server": {
        "service": {
            "type": "LoadBalancer",
        },
    },
    "configs": {
        "params": {
            "server.insecure": True,
        },
    },
}

if argocd_config["admin_password"]:
    if "configs" not in argocd_values:
        argocd_values["configs"] = {}
    configs = argocd_values["configs"]
    if isinstance(configs, dict):
        configs["secret"] = {
            "argocdServerAdminPassword": argocd_config["admin_password"],
        }

if argocd_config["ingress_enabled"]:
    if "server" not in argocd_values:
        argocd_values["server"] = {}
    server = argocd_values["server"]
    if isinstance(server, dict):
        server["ingress"] = {
            "enabled": True,
            "hosts": [argocd_config["ingress_host"]],
        }

argocd = Chart(
    "argocd",
    ChartOpts(
        chart="argo-cd",
        version=argocd_config["chart_version"],
        namespace=argocd_config["namespace"],
        fetch_opts=FetchOpts(
            repo="https://argoproj.github.io/argo-helm",
        ),
        values=argocd_values,
    ),
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[argocd_namespace],
    ),
)

# ============================================================================
# Exports
# ============================================================================
pulumi.export("cert_manager_namespace", cert_manager_namespace.metadata.name)
pulumi.export("external_secrets_namespace", external_secrets_namespace.metadata.name)
pulumi.export("monitoring_namespace", monitoring_namespace.metadata.name)
pulumi.export("logging_namespace", logging_namespace.metadata.name)
pulumi.export("argocd_namespace", argocd_namespace.metadata.name)

pulumi.export("argocd_enabled", True)
pulumi.export("prometheus_enabled", True)
pulumi.export("fluent_bit_enabled", True)
pulumi.export("external_secrets_enabled", True)
pulumi.export("cert_manager_enabled", True)
