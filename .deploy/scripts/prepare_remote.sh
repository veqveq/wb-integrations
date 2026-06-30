#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/../config.sh"

ssh ${SSH_OPTIONS} ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${PROJECT_DIR}"
