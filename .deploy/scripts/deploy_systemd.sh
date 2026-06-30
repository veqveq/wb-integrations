#!/bin/bash
set -euo pipefail

source "$(dirname "$0")/../config.sh"

ssh ${SSH_OPTIONS} ${REMOTE_USER}@${REMOTE_HOST} "

cat > /etc/systemd/system/${CAMERA_ALARM_SERVICE} <<EOF
[Unit]
Description=Camera Alarm Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
Environment=\"PYTHONPATH=${PROJECT_DIR}\"
Environment=\"PROJECT_BASE_PATH=${PROJECT_DIR}\"
Environment="CONFIG_DIR=/etc/wb-integrations"
ExecStart=${PROJECT_DIR}/.venv/bin/python ${PROJECT_DIR}/${CAMERA_ALARM_ENTRY}
Restart=always
RestartSec=3
User=${REMOTE_USER}

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/${NETWORK_CLIENTS_SERVICE} <<EOF
[Unit]
Description=Network Clients Checker Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
Environment=\"PYTHONPATH=${PROJECT_DIR}\"
Environment=\"PROJECT_BASE_PATH=${PROJECT_DIR}\"
Environment="CONFIG_DIR=/etc/wb-integrations"
ExecStart=${PROJECT_DIR}/.venv/bin/python ${PROJECT_DIR}/${NETWORK_CLIENTS_ENTRY}
Restart=always
RestartSec=3
User=${REMOTE_USER}

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

systemctl enable ${CAMERA_ALARM_SERVICE}
systemctl enable ${NETWORK_CLIENTS_SERVICE}

systemctl restart ${CAMERA_ALARM_SERVICE}
systemctl restart ${NETWORK_CLIENTS_SERVICE}
"