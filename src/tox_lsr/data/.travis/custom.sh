#!/bin/bash
# SPDX-License-Identifier: MIT

set -e

#uncomment if you use $ME - otherwise set in utils.sh
#ME=$(basename "$0")
SCRIPTDIR=$(readlink -f "$(dirname "$0")")

. "${SCRIPTDIR}/utils.sh"
. "${SCRIPTDIR}/config.sh"

# Write your custom commands here that should be run when `tox -e custom`:
