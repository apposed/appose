#!/bin/sh

dir=$(dirname "$0")
cd "$dir/.."

# Python/Mamba
mamba env create -f dev-environment.yml

# JavaScript
npm install
