#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="summarizer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["langchain", "ollama"],
    entry_points={
        "console_scripts": [
            "summarizer = summarizer.summarizer:main",
        ],
    }
)
