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

# Finally, run the diff.
echo
echo "== Performing diff =="
appose/bin/diff.sh appose-python appose-java
