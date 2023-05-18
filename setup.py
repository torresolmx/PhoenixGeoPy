import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "PhoenixGeoPy",
    version = "1.0",
    author = "Phoenix Geophysics Ltd.",
    author_email = "pypi@phoenix-geophysics.com",
    description = ("This package enables users to parse and handle Phoenix Geophysics binary time series from the MTU-5C family of receivers."),
    license = "MIT",
    packages=find_packages(),
    long_description=read('README.md'),
    python_requires = ">=3.7",
    install_requires = [
        "numpy>=1.20.0", 
        "matplotlib>=3.4.0"
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    project_urls = {
        "Homepage" : "https://github.com/torresolmx/PhoenixGeoPy",
        "Bug Tracker" : "https://github.com/torresolmx/PhoenixGeoPy/issues"
    }
)
