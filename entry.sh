#!/usr/bin/env bash

# start cron
cron

# wait for selenium
sleep 5

python3 main.py

tail -f /var/log/cron.log