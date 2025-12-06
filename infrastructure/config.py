"""
Configuration helper for Pulumi GKE cluster setup.
Reads configuration from Pulumi config or environment variables.
"""

import pulumi
from typing import Optional


def get_config_value(key: str, default: Optional[str] = None) -> str:
    """Get configuration value from Pulumi config with optional default."""
    config = pulumi.Config()
    return config.get(key) or default or ""


def get_gcp_project() -> str:
    """Get GCP project ID from config."""
    config = pulumi.Config("gcp")
    project = config.require("project")
    return project


def get_gcp_region() -> str:
    """Get GCP region from config, defaults to us-central1."""
    config = pulumi.Config("gcp")
    return config.get("region") or "us-central1"


def get_cluster_name() -> str:
    """Get cluster name from config, defaults to mini-idp-cluster."""
    config = pulumi.Config("cluster")
    return config.get("name") or "mini-idp-cluster"


def get_node_pool_config() -> dict:
    """Get node pool configuration with defaults."""
    config = pulumi.Config("nodePool")
    return {
        "machine_type": config.get("machineType") or "e2-medium",
        "min_nodes": int(config.get("minNodes") or "1"),
        "max_nodes": int(config.get("maxNodes") or "3"),
        "disk_size_gb": int(config.get("diskSizeGb") or "20"),
        "disk_type": config.get("diskType") or "pd-standard",
    }
