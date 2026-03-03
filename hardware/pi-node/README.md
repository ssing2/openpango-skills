# Raspberry Pi Node Blueprint

Automated provisioning for running an OpenPango Node on Raspberry Pi 5.

## Features

- Ubuntu/Debian base image configuration
- Node.js, Python, SQLite installation
- Ollama for local LLM support
- Systemd services for auto-start
- Non-technical user friendly

## Quick Start

1. Flash Ubuntu 22.04 LTS to SD card
2. Insert SD card into Raspberry Pi 5
3. Run: `./provision.sh`
4. OpenPango starts automatically

## Directory Structure

```
hardware/pi-node/
├── README.md           # This file
├── provision.sh        # Main provisioning script
├── ansible/
│   └── playbook.yml    # Ansible playbook
├── systemd/
│   ├── openpango.service
│   └── ollama.service
└── docs/
    └── SETUP.md        # Detailed setup guide
```
