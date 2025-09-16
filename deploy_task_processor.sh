#!/bin/bash
# Envoyou Task Processor Production Deployment Script
# This script sets up the background task processor as a systemd service

set -e

echo "🚀 Deploying Envoyou Background Task Processor"

# Configuration
SERVICE_NAME="envoyou-task-processor"
SERVICE_FILE="/home/husni/PROJECT-ENVOYOU-API/api-envoyou/${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"
PROJECT_DIR="/home/husni/PROJECT-ENVOYOU-API/api-envoyou"
USER="husni"
GROUP="husni"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root${NC}"
   exit 1
fi

echo "📋 Checking prerequisites..."

# Check if Python virtual environment exists
if [ ! -d "${PROJECT_DIR}/venv" ]; then
    echo -e "${RED}Error: Python virtual environment not found at ${PROJECT_DIR}/venv${NC}"
    echo "Please create the virtual environment first:"
    echo "cd ${PROJECT_DIR} && python -m venv venv"
    exit 1
fi

# Check if required Python packages are installed
if ! ${PROJECT_DIR}/venv/bin/python -c "import redis, fastapi" 2>/dev/null; then
    echo -e "${RED}Error: Required Python packages not installed${NC}"
    echo "Please install dependencies:"
    echo "cd ${PROJECT_DIR} && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create envoyou user and group if they don't exist
echo "👤 Setting up service user..."
if ! id -u envoyou > /dev/null 2>&1; then
    sudo useradd --system --shell /bin/false --home-dir /nonexistent --no-create-home envoyou
    echo "Created system user 'envoyou'"
else
    echo "User 'envoyou' already exists"
fi

# Set proper permissions on project directory
echo "🔒 Setting directory permissions..."
sudo chown -R envoyou:envoyou ${PROJECT_DIR}
sudo chmod -R 755 ${PROJECT_DIR}

# Copy service file to systemd directory
echo "📄 Installing systemd service..."
sudo cp ${SERVICE_FILE} ${SYSTEMD_DIR}/

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service
echo "⚡ Enabling service..."
sudo systemctl enable ${SERVICE_NAME}

# Start the service
echo "▶️  Starting service..."
sudo systemctl start ${SERVICE_NAME}

# Wait a moment for the service to start
sleep 3

# Check service status
echo "📊 Checking service status..."
if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}✅ Service started successfully!${NC}"

    # Show service status
    sudo systemctl status ${SERVICE_NAME} --no-pager -l

    echo ""
    echo "📋 Service Management Commands:"
    echo "  Start:   sudo systemctl start ${SERVICE_NAME}"
    echo "  Stop:    sudo systemctl stop ${SERVICE_NAME}"
    echo "  Restart: sudo systemctl restart ${SERVICE_NAME}"
    echo "  Status:  sudo systemctl status ${SERVICE_NAME}"
    echo "  Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
    echo ""
    echo "🔍 Monitor logs with:"
    echo "  sudo journalctl -u ${SERVICE_NAME} -f --since '1 hour ago'"

else
    echo -e "${RED}❌ Service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u ${SERVICE_NAME} -n 50"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Background Task Processor deployment completed!${NC}"
echo ""
echo "The service will automatically restart on system boot and handle failures gracefully."