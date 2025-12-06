"""
Configuration helper for Kubernetes components.
Reads configuration from Pulumi config for Helm chart deployments.
"""

import pulumi
from typing import Dict, Any


def get_gcp_project() -> str:
    """Get GCP project ID from config."""
    config = pulumi.Config("gcp")
    return config.require("project")


def get_gcp_region() -> str:
    """Get GCP region from config, defaults to us-central1."""
    config = pulumi.Config("gcp")
    return config.get("region") or "us-central1"


def get_cluster_name() -> str:
    """Get cluster name from config, defaults to mini-idp-cluster."""
    config = pulumi.Config("cluster")
    return config.get("name") or "mini-idp-cluster"


def get_component_config(component: str) -> Dict[str, Any]:
    """Get component-specific configuration."""
    config = pulumi.Config(f"components.{component}")
    return {
        "enabled": (
            config.get_bool("enabled")
            if config.get_bool("enabled") is not None
            else True
        ),
        "namespace": config.get("namespace") or f"{component}",
        "chart_version": config.get("chartVersion")
        or get_default_chart_version(component),
    }


def get_default_chart_version(component: str) -> str:
    """Get default Helm chart version for component."""
    versions = {
        "argocd": "7.6.0",
        "prometheus": "57.0.0",  # kube-prometheus-stack
        "fluent-bit": "0.21.0",
        "external-secrets": "0.10.0",
        "cert-manager": "v1.13.0",
    }
    return versions.get(component, "latest")


def get_argocd_config() -> Dict[str, Any]:
    """Get ArgoCD specific configuration."""
    config = pulumi.Config("components.argocd")
    return {
        "namespace": config.get("namespace") or "argocd",
        "chart_version": config.get("chartVersion") or "7.6.0",
        "admin_password": config.get("adminPassword") or None,  # Will use default
        "ingress_enabled": config.get_bool("ingressEnabled") or False,
        "ingress_host": config.get("ingressHost") or "argocd.example.com",
    }


def get_prometheus_config() -> Dict[str, Any]:
    """Get Prometheus + Grafana configuration."""
    config = pulumi.Config("components.prometheus")
    return {
        "namespace": config.get("namespace") or "monitoring",
        "chart_version": config.get("chartVersion") or "57.0.0",
        "grafana_admin_password": config.get("grafanaAdminPassword") or "admin",
        "prometheus_retention": config.get("prometheusRetention") or "30d",
        "storage_class": config.get("storageClass") or "standard-rwo",
    }


def get_fluentbit_config() -> Dict[str, Any]:
    """Get Fluent Bit configuration."""
    config = pulumi.Config("components.fluentbit")
    project = get_gcp_project()
    return {
        "namespace": config.get("namespace") or "logging",
        "chart_version": config.get("chartVersion") or "0.21.0",
        "gcp_project": project,
        "log_level": config.get("logLevel") or "info",
    }


def get_external_secrets_config() -> Dict[str, Any]:
    """Get External Secrets Operator configuration."""
    config = pulumi.Config("components.external-secrets")
    project = get_gcp_project()
    return {
        "namespace": config.get("namespace") or "external-secrets-system",
        "chart_version": config.get("chartVersion") or "0.10.0",
        "gcp_project": project,
        "secret_manager_enabled": config.get_bool("secretManagerEnabled") or True,
    }


def get_certmanager_config() -> Dict[str, Any]:
    """Get cert-manager configuration."""
    config = pulumi.Config("components.cert-manager")
    return {
        "namespace": config.get("namespace") or "cert-manager",
        "chart_version": config.get("chartVersion") or "v1.13.0",
        "letsencrypt_email": config.get("letsencryptEmail") or None,
        "letsencrypt_server": config.get("letsencryptServer")
        or "https://acme-v02.api.letsencrypt.org/directory",
    }
