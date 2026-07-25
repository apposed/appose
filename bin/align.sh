#!/bin/sh

cd "$(dirname "$0")/../.."

for impl in appose-python appose-java
do
  echo
  echo "== Generating $impl API =="
  rm -rf "$impl"/api
  "$impl"/bin/api.sh
done

# And now: a bunch of postprocessing hacks to ignore unimportant stuff!

echo
echo "== Postprocessing API files =="
case "$(uname)" in
  Darwin) SED=gsed ;;
  *) SED=sed ;;
esac

dedup() {
  f=$1
  mv "$f" "$f.tmp"
  uniq "$f.tmp" > "$f"
  rm "$f.tmp"
}

# -- global hacks --

find appose-python/api appose-java/api -name '*.api' | while read api
do
  echo "$api"
  $SED -i \
    -e 's;\?;;g' \
    -e 's;abstract def;def;' \
    -e '/^$/d' \
    -e 's;\*\*\([a-z_]\+\): \([a-z_]\+\);\1: dict[str, \2];g' \
    -e 's;\*\([a-z_]\+\): \([a-z_]\+\);\1: list[\2];g' \
    -e 's;str | Path;Path;g' \
    "$api"
done

# -- appose-python hacks --

$SED -i \
  -e '/__init__(self)/d' \
  -e '/_scheme: Incomplete/d' \
  -e '/_content: Incomplete/d' \
  appose-python/api/appose/builder/*.api

rm appose-python/api/appose/_version.api

$SED -i \
  -e '/__cause__/d' \
  appose-python/api/appose/builder/__init__.api

# -- appose-java hacks --

$SED -i \
  -e '/version()/d' \
  appose-java/api/appose/__init__.api

$SED -i \
  -e '/_make_message/d' \
  -e '/_typed_this(self)/d' \
  -e '/env(self, key: str, value: str)/d' \
  appose-java/api/appose/builder/__init__.api
dedup appose-java/api/appose/builder/__init__.api

# -- final normalization pass (reduce cross-cutting noise) --
#
# These transforms apply to BOTH implementations so that incidental
# convention differences do not show up as API diffs:
#   * str and Path are interchangeable for path-like arguments, so unify
#     the standalone Path type to str (Path never appears inside generics
#     here, so a whole-word substitution is safe).
#   * Args is just dict[str, Any]; normalize both spellings to the latter.
#   * Leading underscores (private vs public visibility) are an
#     implementation detail and differ freely between languages, so strip a
#     single leading underscore from defs and classes. Dunder methods
#     (__init__, __enter__, ...) are preserved.
#   * Instance fields, class constants, and module-level type aliases are
#     implementation details whose names, casing, and visibility differ
#     freely (e.g. BASE_PATH vs base_path, _cwd, m_inputs). The comparable
#     API surface is methods, classes, and enum values, so drop bare
#     "name: type" field lines and top-level "name = ..." alias lines.
#     Enum values (indented "NAME = 'value'") are preserved.
#   * Untyped varargs (*args) are equivalent to a list parameter; normalize
#     them to "args: list[Any]" (typed *args are handled by the global hacks).
#   * Parameter names are not part of the (positional) API contract and differ
#     freely (e.g. file(path) vs file(file)), so strip them, keeping types only.
#   * A few names differ only in how acronyms/tokens are split into words
#     (isMacOS -> is_mac_os vs is_macos, etc.); alias the known equivalents.
# After normalizing, names that previously differed only by these
# conventions collapse to duplicates, so dedup each file (order-preserving).
find appose-python/api appose-java/api -name '*.api' | while read api
do
  $SED -i \
    -e 's;\bPath\b;str;g' \
    -e 's;\bArgs\b;dict[str, Any];g' \
    -e 's;: dict);: dict[str, Any]);g' \
    -e 's;\(def \)_\([A-Za-z]\);\1\2;g' \
    -e 's;\(class \)_\([A-Za-z]\);\1\2;g' \
    -e '/^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*:/d' \
    -e '/^[A-Za-z_][A-Za-z0-9_]* = /d' \
    -e '/: None[,)]/d' \
    -e 's;\*\([a-z_][A-Za-z0-9_]*\)\([,)]\);\1: list[Any]\2;g' \
    -e 's;\([(,] \?\)[a-z_][A-Za-z0-9_]*: ;\1;g' \
    -e 's;\bis_mac_os\b;is_macos;g' \
    -e 's;\bun_b_zip2\b;un_bzip2;g' \
    -e 's;\bmicro_mamba_platform\b;micromamba_platform;g' \
    "$api"
  awk '!seen[$0]++' "$api" > "$api.tmp" && mv "$api.tmp" "$api"
done

# Collapse overload families (from optional-parameter expansion) to just
# their minimal- and maximal-arity signatures, on both implementations.
python3 appose/bin/collapse-overloads.py appose-python/api
python3 appose/bin/collapse-overloads.py appose-java/api

# Finally, run the diff.
echo
echo "== Performing diff =="
appose/bin/diff.sh appose-python appose-java
