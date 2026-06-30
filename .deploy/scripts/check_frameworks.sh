#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/../config.sh"

ssh ${SSH_OPTIONS} ${REMOTE_USER}@${REMOTE_HOST} "
    set -e

    echo '--- Checking ${PYTHON_BIN} ---'

    if ! command -v ${PYTHON_BIN} >/dev/null 2>&1; then
        echo '❌ ERROR: ${PYTHON_BIN} is not installed on remote server'
        echo '👉 Required: install python3.12'
        exit 1
    fi

    ${PYTHON_BIN} --version

    echo '--- Checking Poetry ---'

    if ! command -v poetry >/dev/null 2>&1; then
        echo '❌ ERROR: poetry is not installed on remote server'
        echo '👉 Required: install poetry (pip or system package)'
        exit 1
    fi

    poetry --version

    echo '✔ Runtime validation OK'
"