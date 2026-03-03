# Raspberry Pi Setup Guide

This guide walks you through setting up an OpenPango Node on a Raspberry Pi 5.

## Prerequisites

- Raspberry Pi 5 (4GB or 8GB recommended)
- 32GB+ SD Card
- Ubuntu 22.04 LTS 64-bit

## Step 1: Flash Ubuntu to SD Card

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Select "Ubuntu 22.04 LTS (64-bit)"
3. Flash to SD Card

## Step 2: Initial Boot

1. Insert SD Card into Raspberry Pi
2. Connect to network (Ethernet or Wi-Fi)
3. Boot and login (default: ubuntu/ubuntu)

## Step 3: Run Provisioning

```bash
# Clone repository
git clone https://github.com/openpango/openpango-skills.git
cd openpango-skills/hardware/pi-node

# Run provisioning script
./provision.sh
```

## Step 4: Verify Installation

```bash
# Check services
sudo systemctl status openpango
sudo systemctl status ollama

# Check OpenPango
openpango status

# Check Ollama
ollama list
```

## Step 5: Pull a Model

```bash
# Pull a small model for testing
ollama pull llama3.2:1b

# Test
ollama run llama3.2:1b "Hello, OpenPango!"
```

## Accessing OpenPango

- Web UI: http://<pi-ip>:4000
- API: http://<pi-ip>:4000/api

## Troubleshooting

### Ollama not starting

```bash
sudo journalctl -u ollama -f
```

### OpenPango not starting

```bash
sudo journalctl -u openpango -f
```

### Check logs

```bash
tail -f /opt/openpango/logs/openpango.log
```

## Performance Tips

1. Use 8GB RAM model for better performance
2. Enable GPU acceleration (if available)
3. Use SSD instead of SD Card for production

## Security

1. Change default password
2. Enable firewall
3. Use HTTPS with reverse proxy
