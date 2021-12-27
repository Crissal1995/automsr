#!/bin/bash

echo "**********************************"
echo "******** STARTING AUTOMSR ********"
echo "**********************************"

MAX_HOURS_TO_DELAY=2

DELAY_TIME_M=$((1 + $RANDOM % ($MAX_HOURS_TO_DELAY * 60)))
#DELAY_TIME_M=1
DELAY_TIME_S=$(($DELAY_TIME_M * 60))
#DELAY_TIME_S=1

if [ $# -gt 0 ]
then
	echo "Time provided: $1"
	DELAY_TIME_S=$1
fi

cd /home/jiin995/auto_msrewards

echo "[$(date)] Wait $DELAY_TIME_M minutes before run automsr"

sleep $DELAY_TIME_S

echo "[$(date)] Ready to start automsr"

source venv/bin/activate

mkdir -p logs

DISPLAY=:0 python3 main.py  2>&1 | tee -a "logs/automsr-$TS.log"
 
#sudo poweroff -f

