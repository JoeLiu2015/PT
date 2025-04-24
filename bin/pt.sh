#!/bin/bash
# User can configure the Python path here
PYTHON_PATH="/usr/bin/python3"  # Example Python path, modify accordingly
# User can configure the location of the pt module here (directory path)
PT_PATH="../../PT"

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