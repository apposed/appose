#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

# Python
find . -name __pycache__ -type d | while read d
  do rm -rfv "$d"
done
rm -rfv .pytest_cache build dist src/*.egg-info

# Java
mvn clean

# JavaScript
npm clean
