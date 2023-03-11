#!/bin/sh

# Usage examples:
#   bin/test.sh
#   bin/test.sh test_basics.py
#   bin/test.sh test_convert.py::TestConvert::test2DStringArray

set -e

dir=$(dirname "$0")
cd "$dir/.."

py_args=
jv_args=
js_args=
while [ $# -gt 0 ]
do
  case "$1" in
    *.py*) py_args="$py_args src/test/python/$1" ;;
    *.js*) js_args="$js_args src/test/js/$1" ;;
    *) jv_args="$jv_args $1" ;;
  esac
  shift
done

# Python
if [ -z "$py_args" -a -z "$jv_args" -a -z "$js_args" ]
then
  python -m pytest -p no:faulthandler
elif [ "$py_args" ]
then
  python -m pytest -p no:faulthandler $py_args
fi

# Java
if [ -z "$py_args" -a -z "$jv_args" -a -z "$js_args" ]
then
  mvn test
elif [ "$jv_args" ]
then
  mvn test -Dtest=$jv_args
fi

# JavaScript
#TODO
