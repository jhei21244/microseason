#!/bin/bash
# Microseason daily data collection — runs at 7am AEST via cron
cd /home/openclaw/microseason
/usr/bin/python3 collect.py daily >> /home/openclaw/microseason/logs/collect.log 2>&1
echo "--- $(date) ---" >> /home/openclaw/microseason/logs/collect.log
