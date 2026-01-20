#!/bin/bash

# Script to create and install juno systemd service
# This script should be run with sudo/root privileges

set -e  # Exit on error

SERVICE_NAME="juno"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
EXECUTABLE="/home/juno/bin/junocashd"
USER="juno"
GROUP="juno"
WORKING_DIR="/home/juno"

# Create juno user and group if they don't exist
if ! id -u "${USER}" >/dev/null 2>&1; then
    echo "Creating user ${USER}..."
    useradd -r -m -d "${WORKING_DIR}" -s /bin/bash -g "${GROUP}" "${USER}" 2>/dev/null || \
    useradd -r -m -d "${WORKING_DIR}" -s /bin/bash "${USER}"
    echo "User ${USER} created successfully"
else
    echo "User ${USER} already exists"
fi

# Ensure home directory exists with proper permissions
if [ ! -d "${WORKING_DIR}" ]; then
    echo "Creating home directory ${WORKING_DIR}..."
    mkdir -p "${WORKING_DIR}"
    chown "${USER}:${GROUP}" "${WORKING_DIR}"
    echo "Home directory created"
else
    echo "Home directory ${WORKING_DIR} already exists"
fi

# Create bin directory if it doesn't exist
if [ ! -d "${WORKING_DIR}/bin" ]; then
    echo "Creating ${WORKING_DIR}/bin directory..."
    mkdir -p "${WORKING_DIR}/bin"
    chown "${USER}:${GROUP}" "${WORKING_DIR}/bin"
    echo "Bin directory created"
fi

# Download junoup.py
echo "Downloading junoup.py from GitHub..."
curl -L -o "${WORKING_DIR}/bin/junoup.py" "https://raw.githubusercontent.com/finchss/junoup/refs/heads/master/junoup.py"
chmod +x "${WORKING_DIR}/bin/junoup.py"
chown "${USER}:${GROUP}" "${WORKING_DIR}/bin/junoup.py"
echo "junoup.py downloaded and configured"

echo "Creating systemd service file for ${SERVICE_NAME}..."

# Create the service file
cat > "${SERVICE_FILE}" << EOF
[Unit]
Description=Juno Cash Daemon
After=network.target

[Service]
Type=simple
User=${USER}
Group=${GROUP}
WorkingDirectory=${WORKING_DIR}
ExecStartPre=+-/home/juno/bin/junoup.py /home/juno/bin/junocashd
ExecStartPre=+-/bin/chown juno:juno /home/juno/bin/junocashd
ExecStart=${EXECUTABLE}  -randomxfastmode=0 -disablewallet=1
Restart=on-failure
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at ${SERVICE_FILE}"

# Set proper permissions
chmod 644 "${SERVICE_FILE}"
echo "Permissions set on service file"

# Reload systemd daemon
echo "Reloading systemd daemon..."
systemctl daemon-reload

# Run the upgrade script
echo "Running upgrade script..."
/home/juno/bin/junoup.py /home/juno/bin/junocashd
chown "${USER}:${GROUP}" /home/juno/bin/junocashd
echo "Upgrade completed successfully"

# Enable the service
echo "Enabling ${SERVICE_NAME} service to start on boot..."
systemctl enable "${SERVICE_NAME}"

# Start the service
echo "Starting ${SERVICE_NAME} service..."
systemctl start "${SERVICE_NAME}"

echo ""
echo "Juno service has been created, enabled, and started successfully!"
echo ""
echo "To check service status:"
echo "  sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "To view service logs:"
echo "  sudo journalctl -u ${SERVICE_NAME} -f"
echo ""
echo "To stop the service:"
echo "  sudo systemctl stop ${SERVICE_NAME}"
echo ""
echo "To disable the service:"
echo "  sudo systemctl disable ${SERVICE_NAME}"
