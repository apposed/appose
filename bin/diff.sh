#!/bin/sh

#
# Compare API dumps between two Appose implementations.
#

cd "$(dirname "$0")/../.."

stderr() { >&2 printf -- "$@\n"; }
die() { stderr "$@"; exit 1; }

name2dir() {
  case "$1" in
    jl|julia) echo Appose.jl ;;
    j*) echo appose-java ;;
    p*) echo appose-python ;;
    *) echo "$1" ;;
  esac
}

if [ "$#" -eq 2 ]; then
  a=$(name2dir "$1")
  b=$(name2dir "$2")
else
  stderr "Usage: diff.sh <impl1> <impl2>"
  stderr
  stderr "Examples:"
  stderr "- diff.sh java python"
  stderr "- diff.sh j p"
  stderr "- diff.sh jl j"
  stderr "- diff.sh /path/to/appose-java /path/to/Appose.jl"
  die
fi

test -d "$a" || die "Directory '$a' does not exist."
test -d "$b" || die "Directory '$b' does not exist."
test -d "$a" || die "Directory '$a' has no API dump; run \`$a/bin/dump.sh\`"
test -d "$b" || die "Directory '$b' has no API dump; run \`$b/bin/dump.sh\`"

set -x; git diff --no-index "$a/api" "$b/api"
