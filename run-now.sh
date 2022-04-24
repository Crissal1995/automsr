#!/bin/bash

echo "*************************************"
echo "**** Starting AutoMSR run-now.sh ****"
echo "*************************************"

TS=$(date +%F_%R)
mkdir -p logs
DISPLAY=:0 python3 main.py 2>&1 ${AUTOMSR_OPTS} | tee -a "logs/automsr-$TS.log"
