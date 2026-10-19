#!/bin/sh

#
# Compare the APIs of appose-python and appose-java, normalizing away
# differences that stem only from language idioms.
#
# Usage: align.sh [--public]
#
#   --public  Compare only public API, omitting private members.
#

public=
case "$1" in
  --public) public=--public ;;
  "") ;;
  *) >&2 echo "Usage: align.sh [--public]"; exit 1 ;;
esac

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

# -- structural normalization (see normalize-api.py for details) --

python3 appose/bin/normalize-api.py $public appose-python/api
python3 appose/bin/normalize-api.py $public appose-java/api

# -- global hacks --

find appose-python/api appose-java/api -name '*.api' | while read api
do
  echo "$api"
  $SED -i \
    -e 's;\?;;g' \
    -e 's;abstract def;def;' \
    -e '/^$/d' \
    -e 's;\*\*\([a-z_]\+\): \([A-Za-z_]\+\);\1: dict[str, \2];g' \
    -e 's;\*\([a-z_]\+\): \([A-Za-z_]\+\);\1: list[\2];g' \
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

# pytest fixtures have no JUnit counterpart.
find appose-python/api/tests -name conftest.api -exec rm "{}" \;

# Python's import_library takes exactly one of the keyword-only arguments
# path or source, where Java has importLibrary(name, path) and
# importLibrarySource(name, source). Map the former onto the latter, dropping
# the invalid combinations that optional-parameter expansion generated.
# Also, Python's close() returns the exit code as a convenience, which Java's
# cannot, since AutoCloseable.close() is void; its exitValue() suffices.
$SED -i \
  -e '/import_library(self, name: str)/d' \
  -e '/import_library(.*path: .*source: /d' \
  -e '/import_library(.*source: None/d' \
  -e 's;import_library(self, name: str, source: ;import_library_source(self, name: str, source: ;' \
  -e 's;def close(self) -> int:;def close(self) -> None:;' \
  appose-python/api/appose/service.api

# Tools override class constants in Python, but protected methods in Java.
$SED -i \
  -e 's;^    MIN_VERSION: \(.*\)$;    def _min_version(self) -> \1: ...;' \
  -e 's;^    AUTO_UPDATE_VAR: \(.*\)$;    def _auto_update_var(self) -> \1: ...;' \
  appose-python/api/appose/tool/*.api

# Python's SharedMemory inherits its core API from the standard library.
$SED -i \
  -e 's;^class SharedMemory(shared_memory.SharedMemory):;class SharedMemory:\
    def name(self) -> str: ...\
    def size(self) -> int: ...\
    def buf(self) -> bytes: ...\
    def close(self) -> None: ...\
    def unlink(self) -> None: ...;' \
  appose-python/api/appose/shm.api

$SED -i \
  -e '/__cause__/d' \
  appose-python/api/appose/builder/__init__.api

# Python's ServiceProxy forwards via dunder methods, where Java's relies on
# Groovy's dynamic dispatch (getProperty, methodMissing) and named methods.
$SED -i \
  -e 's;def __call__(;def call(;' \
  -e 's;def __dir__(;def dir(;' \
  -e 's;def __getattr__(;def get_property(;' \
  -e 's;def __repr__(;def __str__(;' \
  appose-python/api/appose/util/proxy.api

# -- appose-java hacks --

$SED -i \
  -e '/version()/d' \
  appose-java/api/appose/__init__.api

# Each worker is named after its language, but plays the same role.
# Java's main method receives the command line arguments.
# Java's equals/hashCode overrides correspond to Python dataclass behavior,
# which the stubs do not spell out.
# Java declares functional interfaces where Python uses Callable, e.g. to
# throw checked exceptions.
find appose-java/api -name '*.api' | while read api
do
  $SED -i \
    -e 's;\bGroovyWorker\b;Worker;g' \
    -e 's;def main(args: list\[str\]);def main();' \
    -e '/def equals(self, o: Any) -> bool/d' \
    -e '/def hash_code(self) -> int/d' \
    -e 's;\bActivator\b;Callable[[str], Environment];g' \
    "$api"
done

$SED -i \
  -e 's;^class ServiceProxy(GroovyObjectSupport):;class ServiceProxy:;' \
  -e '/def method_missing(/d' \
  appose-java/api/appose/util/proxy.api

$SED -i \
  -e '/_make_message/d' \
  -e '/_typed_this(self)/d' \
  -e '/env(self, key: str, value: str)/d' \
  appose-java/api/appose/builder/__init__.api

# -- test hacks --

# Test functions are invoked by the test framework, which injects any
# parameters (pytest fixtures such as tmp_path, JUnit's @TempDir) and
# ignores any return value.
find appose-python/api/tests appose-java/api/tests -name '*.api' | while read api
do
  $SED -i \
    -e 's;^def \(test_[A-Za-z0-9_]*\)(.*) -> [A-Za-z]*: \.\.\.$;def \1() -> None: ...;' \
    "$api"
done

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
#   * Private fields, class constants, and module-level type aliases are
#     implementation details whose names, casing, and visibility differ
#     freely (e.g. _cwd, m_inputs). The comparable API surface is methods,
#     classes, and enum values (public fields already became accessor
#     methods in normalize-api.py), so drop bare "name: type" field lines and
#     top-level "name = ..." alias lines.
#     Enum values (indented "NAME = 'value'") are preserved.
#   * Untyped varargs (*args) are equivalent to a list parameter; normalize
#     them to "args: list[Any]" (typed *args are handled by the global hacks).
#   * Parameter names are not part of the (positional) API contract and differ
#     freely (e.g. file(path) vs file(file)), so strip them, keeping types only.
#   * Nullability is not compared ("?" is already stripped), so neither is
#     a "| None" nested inside a generic type.
#   * Untyped dicts are normalized to dict[str, Any].
#   * Python callbacks are typed Callable[[...], Any] where Java uses
#     Consumer, which returns None; normalize the former to the latter.
#   * Java varargs become lists, so Python's tuple[T, ...] does too.
#   * Java spells a timeout (long, TimeUnit) where Python spells it as a
#     float of seconds.
#   * Java's AutoCloseable is Python's context manager protocol, which both
#     dumps already spell out as __enter__/__exit__.
#   * Java proxies need the interface to implement (Class<T> -> T), whereas
#     Python proxies are duck-typed.
#   * A few names differ only in how acronyms/tokens are split into words
#     (isMacOS -> is_mac_os vs is_macos, etc.); alias the known equivalents.
#     Others follow their standard library (returncode for Python's Popen,
#     exitValue for Java's Process); alias those too.
# After normalizing, names that previously differed only by these
# conventions collapse to duplicates, which sort-api.py removes.
find appose-python/api appose-java/api -name '*.api' | while read api
do
  $SED -i \
    -e '/^[A-Za-z_][A-Za-z0-9_]* = /d' \
    -e 's;\bPath\b;str;g' \
    -e 's;\bArgs\b;dict[str, Any];g' \
    -e 's;: dict);: dict[str, Any]);g' \
    -e 's;\(def \)_\([A-Za-z]\);\1\2;g' \
    -e 's;\(class \)_\([A-Za-z]\);\1\2;g' \
    -e '/^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*:/d' \
    -e '/: None[,)]/d' \
    -e 's; | None;;g' \
    -e 's;\bdict\([^[]\|$\);dict[str, Any]\1;g' \
    -e 's;dict\[Any, Any\];dict[str, Any];g' \
    -e 's;Callable\[\[\([^]]*\)\], Any\];Callable[[\1], None];g' \
    -e 's;tuple\[\([^],]*\), \.\.\.\];list[\1];g' \
    -e 's;^\(class [A-Za-z_]*\)(AutoCloseable);\1;' \
    -e 's;(AutoCloseable, ;(;' \
    -e 's;, AutoCloseable);;' \
    -e 's;\*\*\([a-z_][A-Za-z0-9_]*\)\([,)]\);\1: dict[str, Any]\2;g' \
    -e 's;\*\([a-z_][A-Za-z0-9_]*\)\([,)]\);\1: list[Any]\2;g' \
    -e 's;\([(,] \?\)[a-z_][A-Za-z0-9_]*: ;\1;g' \
    -e 's;\bint, TimeUnit\b;float;g' \
    -e 's;, type\[T\]\([,)]\);\1;g' \
    -e 's;-> T:;-> Any:;' \
    -e 's;\breturncode\b;exit_value;g' \
    -e 's;\bd_type\b;dtype;g' \
    -e 's;\bis_mac_os\b;is_macos;g' \
    -e 's;\bun_b_zip2\b;un_bzip2;g' \
    -e 's;\bmicro_mamba_platform\b;micromamba_platform;g' \
    "$api"
done

# Collapse overload families (from optional-parameter expansion) to just
# their minimal- and maximal-arity signatures, on both implementations.
python3 appose/bin/collapse-overloads.py appose-python/api
python3 appose/bin/collapse-overloads.py appose-java/api

# Sort members, so that declaration order does not matter.
python3 appose/bin/sort-api.py appose-python/api
python3 appose/bin/sort-api.py appose-java/api

# Finally, run the diff.
echo
echo "== Performing diff =="
appose/bin/diff.sh appose-python appose-java
