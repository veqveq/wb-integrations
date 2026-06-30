#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/../config.sh"

SOURCE="$(pwd)/"

echo "Deploying project..."
echo "Source : ${SOURCE}"
echo "Target : ${REMOTE_USER}@${REMOTE_HOST}:${PROJECT_DIR}"

rsync -avz --delete \
    -e "ssh ${SSH_OPTIONS}" \
    --exclude='.deploy' \
    --exclude='.git' \
    --exclude='.idea' \
    --exclude='.venv' \
    --exclude='**/logs/**' \
    --exclude='.gitignore' \
    --exclude='README.md' \
    "$SOURCE" \
    "${REMOTE_USER}@${REMOTE_HOST}:${PROJECT_DIR}/"