#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

# Python
python -m build

# Java
mvn clean install

# JavaScript
#TODO
