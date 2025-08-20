#!/bin/bash

# Encode all .txt files describing jeff modules in the input directory and its subdirectories.

# Directory containing the .txt files
script_dir=$(dirname "$0")
input_dir="$script_dir"

# Capnp schema file
schema_file="$script_dir/../impl/capnp/jeff.capnp"

set +e

# Encode each .txt file in the input directory and its subdirectories
find "$input_dir" -name "*.txt" -type f | while read txt_file; do
	base_name=$(basename "$txt_file" .txt)
	dir_name=$(dirname "$txt_file")
	bin_file="$dir_name/$base_name.jeff"

	# Run the capnp encode command
	capnp encode "$schema_file" Module < "$txt_file" > "$bin_file"
	if [ $? -ne 0 ]; then
		echo "Error encoding $txt_file. See above for details." >&2
		echo "---" >&2
	fi
done
