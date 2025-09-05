"""Setup script for the AltWallet Python SDK."""

from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="altwallet-sdk",
    version="1.0.0",
    author="AltWallet Team",
    author_email="team@altwallet.com",
    description="AltWallet Checkout Agent Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/altwallet/checkout-agent",
    project_urls={
        "Bug Tracker": "https://github.com/altwallet/checkout-agent/issues",
        "Documentation": "https://github.com/altwallet/checkout-agent#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
        ],
    },
    keywords=[
        "altwallet",
        "checkout",
        "payment",
        "credit-cards",
        "recommendations",
        "sdk",
    ],
    include_package_data=True,
    zip_safe=False,
)
