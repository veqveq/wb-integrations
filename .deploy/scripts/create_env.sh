#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/../config.sh"

ssh ${SSH_OPTIONS} ${REMOTE_USER}@${REMOTE_HOST} "
    set -e

    export PATH=\$HOME/.local/bin:\$PATH
    poetry config virtualenvs.in-project true

    cd ${PROJECT_DIR}
    poetry install --no-interaction --no-ansi
"
