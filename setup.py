from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="archon",
    version="0.1.0",
    author="srujanasru0521-create",
    author_email="your@email.com",
    description="Archon AI - The Self-Governing Knowledge Graph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/srujanasru0521-create/archon",

    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
    python_requires=">=3.9",
    install_requires=[
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.4.0",
        "typer>=0.9.0",
        "rich>=13.0.0",
        "tree-sitter>=0.20.0",
        "tree-sitter-python>=0.20.0",
        "sentence-transformers>=2.2.0",
        "torch>=2.0.0",
        "lancedb>=0.3.0",
        "watchdog>=3.0.0",
        "numpy>=1.24.0",
        "tqdm>=4.66.0",
        "pyyaml>=6.0.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "archon=archon.cli:app",
        ],
    },
)
