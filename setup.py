"""
Setup script for Mini-IDP.
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="mini-idp",
    version="0.1.0",
    author="Mini-IDP Contributors",
    description="Deploy applications to Kubernetes with no YAML required",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mini-idp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "mini-idp=cli.main:main",
        ],
    },
)
