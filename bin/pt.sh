#!/bin/bash
# User can configure the Python path here
PYTHON_PATH="/usr/bin/python3"  # Example Python path, modify accordingly
# User can configure the location of the pt module here (directory path)
PT_PATH="../../PT"


# Get the right absolute path for PT module
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REL_PATH="../../PT"
if command -v realpath >/dev/null 2>&1; then
    PT_PATH="$(realpath "$SCRIPT_DIR/$REL_PATH")"
else
    PT_PATH="$(readlink -f "$SCRIPT_DIR/$REL_PATH")"
fi


# Check if the configured Python path exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: The configured Python path '$PYTHON_PATH' does not exist."
    exit 1
fi

# Check if the configured pt module directory exists
if [ ! -d "$PT_PATH" ]; then
    echo "Error: The pt module directory '$PT_PATH' does not exist."
    exit 1
fi

# If both paths exist, execute the pt module with Python
# echo "Using Python path '$PYTHON_PATH' to execute the pt module from '$PT_PATH'..."
"$PYTHON_PATH" "$PT_PATH" "$@"