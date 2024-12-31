from setuptools import find_packages, setup

setup(
    name="ocr-module",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "azure-ai-documentintelligence",
        "openai",
        "pylatex",
        "pypdf2",
    ],
    python_requires=">=3.8",
    description="OCRと翻訳機能を提供するPythonモジュール",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/ridgebull/ocr-module",
)
