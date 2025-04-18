from setuptools import setup, find_packages

setup(
    name="ai_studio_package",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "numpy",
        "transformers",
        "sentence-transformers",
        "praw",
        "faiss-cpu",
    ],
) 