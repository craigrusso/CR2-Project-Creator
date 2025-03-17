#!/bin/bash
# Script to sign a specific component of the Echelon app

# Exit on error
set -e

# Certificate identity
CERT_ID="Developer ID Application: craig russo (5926DW86QY)"

# Check if component path was provided
if [ -z "$1" ]; then
    echo "Error: Please provide the path to the component to sign"
    echo "Usage: $0 path/to/component"
    exit 1
fi

COMPONENT_PATH="$1"

# Check if component exists
if [ ! -f "$COMPONENT_PATH" ]; then
    echo "Error: Component not found at $COMPONENT_PATH"
    exit 1
fi

echo "Signing component: $COMPONENT_PATH"
codesign --force --sign "$CERT_ID" --timestamp "$COMPONENT_PATH"

echo "Component signed successfully" 