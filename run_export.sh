#!/bin/bash

# Granola Exporter Wrapper
# This script runs the Python exporter to update your meeting notes.

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the python script with any arguments passed to this wrapper
echo "Starting Granola Export..."
python3 "$SCRIPT_DIR/granola_exporter.py" "$@"

echo "Done."
