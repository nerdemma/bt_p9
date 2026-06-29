![P9 Bluetooth Media Monitor](docs/bt_p9.jpeg)

# P9 Bluetooth Media Monitor & TTS Agent 🎧🚀

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License: GPL](https://img.shields.io/badge/License-GPL-green.svg?style=flat-square)](LICENSE)
[![Platform: Debian/Linux](https://img.shields.io/badge/platform-Debian%2FLinux-red?style=flat-square&logo=linux)](https://www.debian.org/)
[![Bluetooth 5.0+](https://img.shields.io/badge/bluetooth-5.0%2B-blue?style=flat-square&logo=bluetooth)](https://www.bluetooth.com/)
[![Async Ready](https://img.shields.io/badge/async-ready-brightgreen?style=flat-square)](#-features)
[![Zero CPU Idle](https://img.shields.io/badge/idle%20cpu-0%25-brightgreen?style=flat-square)](#-features)

A lightweight asynchronous daemon written in Python for **Debian/Linux** designed to automate multimedia control and provide a voice notification system (*Text-to-Speech*) by reactively interacting with the Bluetooth subsystem (`BlueZ`) and MPRIS controllers.

---

## ✨ Key Features

- **🎯 Reactive Monitoring (Event-Driven):** Listens to kernel events through `bluetoothctl monitor` using `asyncio`. No continuous polling—achieving **0% CPU** usage at rest.
- **⚡ Cold Start Synchronization:** Verifies the real connection state of P9 headphones immediately on service startup.
- **🎵 Intelligent Multimedia Control:** Automatically pauses music when headphones disconnect (via `playerctl`) and resumes playback upon reconnection.
- **🔊 Private Notification Server (IPC):** Exposes a Unix Named Pipe (`FIFO`). Any system script can send text in real-time for the daemon to convert to voice (`gTTS`) and play exclusively through the headphones in isolation.
- **⚙️ Systemd Integration:** Simple service deployment for persistent background operation.
- **🛡️ Lightweight & Secure:** Minimal dependencies, isolated Python environment, no external network calls.

## 📋 Table of Contents

- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Configuration](#⚙️-configuration)
- [Deployment as Systemd Service](#-deployment-as-systemd-service)
- [Integration & Notifications](#-integration--notifications)
- [Use Cases](#-use-cases)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🛠️ System Requirements

The script leverages native Linux ecosystem tools:

```bash
sudo apt update
sudo apt install bluez playerctl mpv python3 python3-venv -y
```

| Component | Purpose |
|-----------|---------|
| **bluez** | Linux Bluetooth stack management |
| **playerctl** | Universal music player control for Linux (Spotify, VLC, browsers, etc.) |
| **mpv** | Minimal multimedia player for TTS audio output |
| **python3** | Python 3.8+ interpreter |
| **python3-venv** | Isolated virtual environment tool |

### Compatibility

- ✅ **Debian 11+** (Bullseye and later)
- ✅ **Ubuntu 20.04+** (Focal and later)
- ✅ **Raspberry Pi OS** (with Bluetooth hardware)
- ✅ All Bluetooth 5.0+ compatible headphones

---

## 🚀 Installation

### 1. Clone Repository & Setup Directory

```bash
mkdir -p ~/projects/bt_p9
cd ~/projects/bt_p9
git clone <your-repo-url> .
```

### 2. Configure Isolated Virtual Environment

To avoid conflicts with Debian's package manager (`externally-managed-environment`), we encapsulate dependencies:

```bash
python3 -m venv ~/.p9_env
~/.p9_env/bin/pip install -U pip
~/.p9_env/bin/pip install gTTS
```

**Why a Virtual Environment?**
- ✅ Isolates Python dependencies from system packages
- ✅ Avoids permission issues with `pip` on managed Debian systems
- ✅ Makes the daemon easily portable across machines

---

## ⚙️ Configuration

### Get Your P9 Headphones MAC Address

1. **Power on your P9 headphones**
2. **Run the following command** to list all Bluetooth devices:

```bash
bluetoothctl devices
```

You should see output similar to:
```
Device 00:00:00:00:00:00 P9 Headphones
```

3. **Edit `main.py`** and update the global constant with your MAC address:

```python
TARGET_MAC = "00:00:00:00:00:00"  # Replace with your actual MAC
```

> **💡 Tip:** You can verify the MAC is correct by running `bluetoothctl info 00:00:00:00:00:00`

---

## 🔧 Deployment as Systemd Service

To keep the script running persistently in the background under your user session:

### 1. Create Service Configuration File

```bash
mkdir -p ~/.config/systemd/user/
nano ~/.config/systemd/user/p9-monitor.service
```

### 2. Paste the Service Definition

Replace `username` with your actual username:

```ini
[Unit]
Description=P9 Headphones Connection Monitor with TTS
After=bluetooth.target
Documentation=https://github.com/bt_p9

[Service]
Type=simple
ExecStart=/home/username/.p9_env/bin/python3 /home/username/projects/bt_p9/main.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### 3. Reload and Activate Service

```bash
# Reload systemd daemon
systemctl --user daemon-reload

# Enable auto-start on login
systemctl --user enable p9-monitor.service

# Start the service now
systemctl --user start p9-monitor.service
```

### 4. Monitor Logs in Real-Time

```bash
# Check current service status
systemctl --user status p9-monitor.service

# Stream logs live (Ctrl+C to exit)
journalctl --user -u p9-monitor.service -f

# View last 50 lines
journalctl --user -u p9-monitor.service -n 50
```

---

## 🔔 Integration & Notifications

The architecture uses an inter-process communication channel (IPC Named Pipe) at `/tmp/p9_notifications`. The service processes text input **only if you're wearing the headphones**.

### From Terminal (CLI)

```bash
echo "Hello Emmanuel, the notification system is operational." > /tmp/p9_notifications
```

### From Python Script

Integrate voice alerts into your development projects (e.g., server monitoring, low battery alerts, webhooks):

```python
import os

def send_p9_alert(message: str) -> bool:
    """
    Send a voice notification to the P9 daemon.
    
    Args:
        message: Text to be converted to speech
        
    Returns:
        True if successful, False if pipe doesn't exist
    """
    pipe_path = "/tmp/p9_notifications"
    try:
        with open(pipe_path, "w") as pipe:
            pipe.write(f"{message}\n")
        return True
    except FileNotFoundError:
        print(f"Warning: Pipe {pipe_path} not found. Is the service running?")
        return False

# Usage examples
send_p9_alert("Alert: Local database backup completed.")
send_p9_alert("Critical: Server CPU usage exceeded 90%.")
send_p9_alert("Reminder: You have 3 pending pull requests.")
```

### From Shell Scripts

```bash
#!/bin/bash

PIPE="/tmp/p9_notifications"

if [ -p "$PIPE" ]; then
    echo "System alert: Updates available for Debian packages." > "$PIPE"
else
    echo "Error: P9 daemon not running"
    exit 1
fi
```

---

## 📊 Use Cases

Practical integration examples:

### 🔋 System Alerts
- Low battery warnings
- Available updates notifications
- Disk space warnings
- System temperature alerts

### 📡 Server Monitoring
- Critical service failures
- Resource utilization thresholds
- Deployment notifications
- Health check failures

### 🌐 Webhook Integration
- GitHub/GitLab notifications
- CI/CD pipeline status
- Monitoring service alerts (Grafana, Prometheus)
- Custom API webhooks

### 🤖 Automation
- Smart home alerts
- Task completion notifications
- Scheduled reminders
- Conditional triggers

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Service won't start** | Check logs: `journalctl --user -u p9-monitor.service -f` |
| **Headphones not recognized** | Verify MAC address is correct in `main.py` |
| **No sound in notifications** | Ensure `mpv` is installed and headphones are connected |
| **Permission denied errors** | Fix venv permissions: `chmod +x ~/.p9_env/bin/python3` |
| **Service crashes on startup** | Run manually to see errors: `~/.p9_env/bin/python3 /home/username/projects/bt_p9/main.py` |
| **Named pipe doesn't exist** | Check if daemon is running: `systemctl --user status p9-monitor.service` |
| **Notification delays** | This is normal; gTTS requires ~1-2 seconds for synthesis |

### Debug Mode

For detailed troubleshooting, modify `main.py` to add logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("Headphones connected: BA:0F:2B:68:94:F7")
```

---

## 📦 Project Structure

```
bt_p9/
├── main.py                 # Core daemon script
├── README.md              # This file
├── LICENSE                # GPL License
├── docs/                 # pics and website 
└── .gitignore            # Git exclusions
```

---

## 🤝 Contributing

Contributions are welcome! To help improve this project:

1. **Fork** the repository
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit changes** (`git commit -m 'Add amazing feature'`)
4. **Push to branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Ideas for Enhancement
- [ ] Configuration file support (YAML/JSON)
- [ ] Multiple headphone device support
- [ ] Custom TTS voice selection
- [ ] Message priority queue
- [ ] Notification logging/history
- [ ] Prometheus metrics export

---

## 📝 License

Licensed under the **GPL License**. See [LICENSE](LICENSE) file for details.

> Free for personal, commercial, and educational use. Modifications and distributions are permitted under the terms of the license.

---

## 🆘 Support & Contact

**Have questions?** Open an [issue](../../issues) on the repository.

**Found a bug?** Please report it with:
- Your Debian/Linux version
- Python version (`python3 --version`)
- Error logs from `journalctl`
- Steps to reproduce

**Want to contribute?** We'd love your pull requests! 🎉

---

## 🔗 Related Projects

- [BlueZ](http://www.bluez.org/) - Official Linux Bluetooth stack
- [gTTS](https://github.com/pndurette/gTTS) - Google Text-to-Speech
- [playerctl](https://github.com/altdesktop/playerctl) - Music player control
- [mpv](https://mpv.io/) - Multimedia player

---

**Made with ❤️ for Linux audio enthusiasts**
