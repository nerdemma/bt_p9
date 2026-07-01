#!/bin/bash

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"

systemctl --user reset-failed p9-monitor.service
systemctl --user daemon-reload
systemctl --user start p9-monitor.service
