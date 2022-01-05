#!/bin/bash

echo "**********************************"
echo "******** STARTING AUTOMSR ********"
echo "**********************************"

MAX_HOURS_TO_DELAY=2

DELAY_TIME_M=$((1 + $RANDOM % ($MAX_HOURS_TO_DELAY * 60)))
DELAY_TIME_S=$(($DELAY_TIME_M * 60))
TS=$(date +%F_%R)

AUTOMSR_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ $# -gt 0 ]
then
	echo "Time provided: $1"
	DELAY_TIME_S=$1
	DELAY_TIME_M=$(($DELAY_TIME_S / 60))
fi

REMAINDER=$(($DELAY_TIME_S % 60))
echo "[$(date)] Wait $DELAY_TIME_M min, $REMAINDER sec before AutoMSR starts"

sleep $DELAY_TIME_S
echo "[$(date)] Ready to start AutoMSR"

cd ${AUTOMSR_PATH}

possible_venvs=( ".venv" "venv" "virtualenv" )
for venv in "${possible_venvs[@]}"
do
	if [[ -f "$venv/bin/activate" ]]; then
		echo "Sourcing $venv/bin/activate"
		source "$venv/bin/activate"
		break
	fi
done

mkdir -p logs
DISPLAY=:0 python3 main.py 2>&1 | tee -a "logs/automsr-$TS.log"
