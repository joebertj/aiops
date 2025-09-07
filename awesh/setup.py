#!/usr/bin/env python3
"""
Setup script for awesh - AI-aware interactive shell
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="awesh",
    version="0.1.0",
    author="AI Operations Team",
    author_email="aiops@example.com",
    description="AI-aware interactive shell - 'AI by default, Bash when I mean Bash'",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aiops/awesh",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Shells",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "awesh=awesh.main:cli_main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
