#!/bin/bash

# Remote server
REMOTE_USER="root"
REMOTE_HOST="192.168.1.30"

# Paths
PROJECT_DIR="/mnt/data/wb-integrations"

# Frameworks
PYTHON_BIN="python3.12"

# SSH
SSH_OPTIONS="-o StrictHostKeyChecking=accept-new"

# Services
CAMERA_ALARM_SERVICE="camera_alarm.service"
NETWORK_CLIENTS_SERVICE="network_clients_checker.service"
CAMERA_LIGHT_SENSOR_SERVICE="camera_light_sensor.service"

# Applications
CAMERA_ALARM_ENTRY="security/camera_alarm/service/camera_alarm.py"
NETWORK_CLIENTS_ENTRY="security/network_clients_checker/service/network_clients_checker.py"
CAMERA_LIGHT_SENSOR_ENTRY="sensor/camera_light_sensor/service/camera_light_sensor.py"
