# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import find_packages
from setuptools import setup

__version__ = "0.1.0"
ROOT_DIR = Path(".")

with open(str(ROOT_DIR / "README.md")) as readme:
    long_description = readme.read()

setup(
    name="Flask-Model-Management",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    author="jackwardell",
    author_email="jack@wardell.xyz",
    url="https://github.com/jackwardell/Flask-Model-Management",
    description="Extension to manage SQLAlchemy models in Flask",
    long_description=long_description,
    long_description_content_type="text/markdown",
    test_suite="tests",
    install_requires=["Flask", "Flask-SQLAlchemy", "WTForms", "Flask-WTF", "attrs"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
    ],
    keywords="python",
    python_requires=">=3.6",
)
