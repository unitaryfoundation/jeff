#!/usr/bin/env bash
# Encode all hand-crafted .txt fixtures in negative/encode/ to their target test directories.
#
# Run from anywhere:
#   tools/verifier/tests/encode_test_cases.sh
#
# Requires the capnp CLI tool to be installed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCHEMA="$REPO_ROOT/impl/capnp/jeff.capnp"
ENCODED_DIR="$SCRIPT_DIR/negative/encode"

if ! command -v capnp &>/dev/null; then
    echo "error: capnp not found. Install the Cap'n Proto CLI tools." >&2
    exit 1
fi

echo "Encoding hand-crafted test fixtures..."

while IFS= read -r -d '' src; do
    # src is e.g. .../negative/encode/bounds/op_input_oob.txt
    rel="${src#$ENCODED_DIR/}"            # bounds/op_input_oob.txt
    subdir="$(dirname "$rel")"            # bounds
    base="$(basename "$rel" .txt)"        # op_input_oob
    dst_dir="$SCRIPT_DIR/negative/$subdir"
    dst="$dst_dir/$base.jeff"
    mkdir -p "$dst_dir"
    capnp encode "$SCHEMA" Module < "$src" > "$dst"
    echo "  encoded: negative/$subdir/$base.jeff"
done < <(find "$ENCODED_DIR" -name "*.txt" -print0 | sort -z)

echo "Done."
