#!/bin/bash
set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>" >&2
    exit 1
fi

dir="$1"
schema="$(dirname "$0")/../../../impl/capnp/jeff.capnp"

find "$dir" -name "*.txt" -type f | while read -r txt; do
    jeff="${txt%.txt}.jeff"
    if ! capnp encode "$schema" Module < "$txt" > "$jeff"; then
        echo "Error encoding $txt" >&2
    fi
done
