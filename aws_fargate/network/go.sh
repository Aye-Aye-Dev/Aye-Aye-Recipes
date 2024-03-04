#!/bin/bash
if [ $1 ]
    then
    export STACK_LABEL=$1

else
    echo "Stack name needed as command line argument"
    echo "e.g."
    echo "./go.sh dev"
    exit 1
fi

set -euo pipefail

pulumi stack select $STACK_LABEL
pulumi up
