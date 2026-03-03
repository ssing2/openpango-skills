#!/bin/bash
#
# provision.sh - Automated provisioning for OpenPango Node on Raspberry Pi 5
#
# This script sets up a complete OpenPango environment including:
# - Node.js and Python
# - SQLite database
# - Ollama for local LLM support
# - OpenPango services
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Raspberry Pi
check_platform() {
    if [ -f /proc/device-tree/model ]; then
        MODEL=$(cat /proc/device-tree/model)
        if [[ "$MODEL" == *"Raspberry Pi"* ]]; then
            log_info "Detected: $MODEL"
            return 0
        fi
    fi
    log_warn "Not running on Raspberry Pi. Some features may not work."
}

# Update system
update_system() {
    log_info "Updating system packages..."
    sudo apt-get update -y
    sudo apt-get upgrade -y
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    
    # Build tools
    sudo apt-get install -y \
        build-essential \
        curl \
        wget \
        git \
        sqlite3 \
        libsqlite3-dev \
        python3 \
        python3-pip \
        python3-venv \
        firefox-esr \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libatspi2.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libwayland-client0 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        xdg-utils
}

# Install Node.js
install_nodejs() {
    log_info "Installing Node.js..."
    
    if command -v node &> /dev/null; then
        log_info "Node.js already installed: $(node --version)"
        return 0
    fi
    
    # Install Node.js 20 LTS
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    log_info "Node.js installed: $(node --version)"
    log_info "npm installed: $(npm --version)"
}

# Install Ollama
install_ollama() {
    log_info "Installing Ollama..."
    
    if command -v ollama &> /dev/null; then
        log_info "Ollama already installed"
        return 0
    fi
    
    curl -fsSL https://ollama.com/install.sh | sh
    
    log_info "Ollama installed"
}

# Setup Python environment
setup_python() {
    log_info "Setting up Python environment..."
    
    python3 -m pip install --upgrade pip
    python3 -m pip install \
        sqlite3 \
        requests \
        aiohttp
}

# Install OpenPango
install_openpango() {
    log_info "Installing OpenPango..."
    
    if command -v openpango &> /dev/null; then
        log_info "OpenPango already installed"
        return 0
    fi
    
    # Install OpenPango CLI globally
    npm install -g openpango
    
    log_info "OpenPango installed: $(openpango --version)"
}

# Setup systemd services
setup_services() {
    log_info "Setting up systemd services..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Install OpenPango service
    sudo cp "$SCRIPT_DIR/systemd/openpango.service" /etc/systemd/system/
    
    # Install Ollama service (if not already installed)
    if [ ! -f /etc/systemd/system/ollama.service ]; then
        sudo cp "$SCRIPT_DIR/systemd/ollama.service" /etc/systemd/system/
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable openpango
    sudo systemctl enable ollama
    
    log_info "Services configured"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    sudo systemctl start ollama
    sleep 5  # Wait for Ollama to start
    
    sudo systemctl start openpango
    
    log_info "Services started"
}

# Print status
print_status() {
    log_info "=== OpenPango Node Status ==="
    log_info "Node.js: $(node --version 2>/dev/null || echo 'not installed')"
    log_info "Python: $(python3 --version 2>/dev/null || echo 'not installed')"
    log_info "Ollama: $(ollama --version 2>/dev/null || echo 'not installed')"
    log_info "OpenPango: $(openpango --version 2>/dev/null || echo 'not installed')"
    
    log_info ""
    log_info "Services:"
    systemctl is-active openpango 2>/dev/null && log_info "  openpango: running" || log_warn "  openpango: not running"
    systemctl is-active ollama 2>/dev/null && log_info "  ollama: running" || log_warn "  ollama: not running"
    
    log_info ""
    log_info "=== Provisioning Complete ==="
    log_info "OpenPango Node is now running on your Raspberry Pi!"
    log_info "Access the dashboard at: http://$(hostname -I | awk '{print $1}'):4000"
}

# Main function
main() {
    log_info "Starting OpenPango Node provisioning..."
    
    check_platform
    update_system
    install_dependencies
    install_nodejs
    install_ollama
    setup_python
    install_openpango
    setup_services
    start_services
    print_status
}

# Run main
main "$@"
