#!/bin/bash
cd /home/archuserbtw/AI-BASED-DEVICE-HEALTH-MONITOR
venv/bin/python App.py
cd /home/archuserbtw/AI-BASED-DEVICE-HEALTH-MONITOR/data
../venv/bin/python -m http.server 8081
