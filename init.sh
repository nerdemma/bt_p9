#!/bin/bash

systemctl --user reset-failed p9-monitor.service
systemctl --user daemon-reload
systemctl --user start p9-monitor.service