#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

# Python
black src tests
isort src tests
python -m flake8 src tests
validate-pyproject pyproject.toml

# Java
mvn formatter:format
mvn impsort:sort

# JavaScript
#TODO
