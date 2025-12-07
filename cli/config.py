"""
Configuration management for Mini-IDP CLI.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def get_config_dir() -> Path:
    """Get the configuration directory."""
    config_dir = Path.home() / ".mini-idp"
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.yaml"


def get_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment variables.

    Args:
        config_path: Optional path to config file

    Returns:
        Configuration dictionary
    """
    config_file = config_path or get_config_file()

    # Start with defaults
    config = {
        "initialized": False,
        "kubeconfig": os.getenv("KUBECONFIG"),
        "default_namespace": os.getenv("MINI_IDP_NAMESPACE", "default"),
        "default_cluster": os.getenv("MINI_IDP_CLUSTER"),
        "argocd_namespace": os.getenv("ARGOCD_NAMESPACE", "argocd"),
        "templates_dir": os.getenv(
            "MINI_IDP_TEMPLATES_DIR",
            str(Path(__file__).parent.parent / "templates"),
        ),
    }

    # Load from file if it exists
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                file_config = yaml.safe_load(f) or {}
                config.update(file_config)
                config["initialized"] = True
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")

    # Override with environment variables
    if os.getenv("KUBECONFIG"):
        config["kubeconfig"] = os.getenv("KUBECONFIG")
    if os.getenv("MINI_IDP_NAMESPACE"):
        config["default_namespace"] = os.getenv("MINI_IDP_NAMESPACE")
    if os.getenv("ARGOCD_NAMESPACE"):
        config["argocd_namespace"] = os.getenv("ARGOCD_NAMESPACE")

    return config


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def init_config() -> Dict[str, Any]:
    """
    Initialize configuration interactively.

    Returns:
        Initialized configuration dictionary
    """
    import click

    config = get_config()

    click.echo("Mini-IDP Configuration Setup")
    click.echo("=" * 40)

    # Get kubeconfig
    kubeconfig = click.prompt(
        "Path to kubeconfig",
        default=config.get("kubeconfig") or "~/.kube/config",
        type=click.Path(),
    )
    config["kubeconfig"] = os.path.expanduser(kubeconfig)

    # Get default namespace
    namespace = click.prompt(
        "Default namespace",
        default=config.get("default_namespace", "default"),
    )
    config["default_namespace"] = namespace

    # Get ArgoCD namespace
    argocd_ns = click.prompt(
        "ArgoCD namespace",
        default=config.get("argocd_namespace", "argocd"),
    )
    config["argocd_namespace"] = argocd_ns

    # Get templates directory
    templates_dir = click.prompt(
        "Templates directory",
        default=config.get("templates_dir"),
        type=click.Path(exists=True, file_okay=False, dir_okay=True),
    )
    config["templates_dir"] = templates_dir

    config["initialized"] = True
    save_config(config)

    return config


def get_kubeconfig_path(config: Dict[str, Any]) -> Optional[str]:
    """
    Get the kubeconfig path from config or environment.

    Args:
        config: Configuration dictionary

    Returns:
        Path to kubeconfig file or None
    """
    kubeconfig = config.get("kubeconfig") or os.getenv("KUBECONFIG")
    if kubeconfig:
        return os.path.expanduser(kubeconfig)
    return None
