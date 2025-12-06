"""
Main Pulumi program for GKE cluster infrastructure.
Creates a GKE cluster with:
- Autoscaling node pools
- Workload Identity enabled
- Network policies configured
- Monitoring/logging enabled
"""

import pulumi
import pulumi_gcp as gcp

from config import (
    get_gcp_project,
    get_gcp_region,
    get_cluster_name,
    get_node_pool_config,
)

# Get configuration
project = get_gcp_project()
region = get_gcp_region()
cluster_name = get_cluster_name()
node_pool_config = get_node_pool_config()

# Enable required APIs
compute_api = gcp.projects.Service(
    "compute-api",
    service="compute.googleapis.com",
    project=project,
    disable_on_destroy=False,
)

container_api = gcp.projects.Service(
    "container-api",
    service="container.googleapis.com",
    project=project,
    disable_on_destroy=False,
    opts=pulumi.ResourceOptions(depends_on=[compute_api]),
)

monitoring_api = gcp.projects.Service(
    "monitoring-api",
    service="monitoring.googleapis.com",
    project=project,
    disable_on_destroy=False,
    opts=pulumi.ResourceOptions(depends_on=[container_api]),
)

logging_api = gcp.projects.Service(
    "logging-api",
    service="logging.googleapis.com",
    project=project,
    disable_on_destroy=False,
    opts=pulumi.ResourceOptions(depends_on=[container_api]),
)

# Get default network
default_network = gcp.compute.get_network(name="default", project=project)

# Create GKE cluster
cluster = gcp.container.Cluster(
    cluster_name,
    name=cluster_name,
    location=region,
    project=project,
    initial_node_count=1,
    remove_default_node_pool=True,
    network=default_network.name,
    subnetwork=default_network.name,
    # Enable Workload Identity
    workload_identity_config=gcp.container.ClusterWorkloadIdentityConfigArgs(
        workload_pool=f"{project}.svc.id.goog",
    ),
    # Enable network policies
    network_policy=gcp.container.ClusterNetworkPolicyArgs(
        enabled=True,
        provider="CALICO",
    ),
    # Enable monitoring and logging
    logging_service="logging.googleapis.com/kubernetes",
    monitoring_service="monitoring.googleapis.com/kubernetes",
    addons_config=gcp.container.ClusterAddonsConfigArgs(
        network_policy_config=gcp.container.ClusterAddonsConfigNetworkPolicyConfigArgs(
            disabled=False,
        ),
    ),
    # Enable autoscaling for the cluster
    enable_autopilot=False,
    # Resource labels
    resource_labels={
        "managed-by": "pulumi",
        "environment": "production",
    },
    opts=pulumi.ResourceOptions(
        depends_on=[
            container_api,
            monitoring_api,
            logging_api,
        ],
    ),
)

# Create autoscaling node pool
node_pool = gcp.container.NodePool(
    f"{cluster_name}-node-pool",
    name=f"{cluster_name}-node-pool",
    location=region,
    cluster=cluster.name,
    project=project,
    node_count=node_pool_config["min_nodes"],
    autoscaling=gcp.container.NodePoolAutoscalingArgs(
        min_node_count=node_pool_config["min_nodes"],
        max_node_count=node_pool_config["max_nodes"],
    ),
    management=gcp.container.NodePoolManagementArgs(
        auto_repair=True,
        auto_upgrade=True,
    ),
    node_config=gcp.container.NodePoolNodeConfigArgs(
        machine_type=node_pool_config["machine_type"],
        disk_size_gb=node_pool_config["disk_size_gb"],
        disk_type=node_pool_config["disk_type"],
        oauth_scopes=[
            "https://www.googleapis.com/auth/cloud-platform",
        ],
        # Enable Workload Identity on nodes
        workload_metadata_config=(
            gcp.container.NodePoolNodeConfigWorkloadMetadataConfigArgs(
                mode="GKE_METADATA",
            )
        ),
        labels={
            "managed-by": "pulumi",
        },
    ),
    opts=pulumi.ResourceOptions(depends_on=[cluster]),
)

# Export cluster information
pulumi.export("cluster_name", cluster.name)
pulumi.export("cluster_endpoint", cluster.endpoint)
pulumi.export("cluster_location", cluster.location)
pulumi.export(
    "cluster_workload_identity_pool",
    cluster.workload_identity_config.workload_pool,
)
pulumi.export("node_pool_name", node_pool.name)
pulumi.export("node_pool_min_nodes", node_pool_config["min_nodes"])
pulumi.export("node_pool_max_nodes", node_pool_config["max_nodes"])
