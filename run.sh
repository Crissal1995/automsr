#!/bin/bash

echo "*********************************"
echo "**** Starting AutoMSR run.sh ****"
echo "*********************************"

MAX_HOURS_TO_DELAY=2

DELAY_TIME_M=$((1 + RANDOM % (MAX_HOURS_TO_DELAY * 60)))
DELAY_TIME_S=$((DELAY_TIME_M * 60))

AUTOMSR_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

if [ $# -gt 0 ]
then
	echo "Time provided: $1"
	DELAY_TIME_S=$1
	DELAY_TIME_M=$((DELAY_TIME_S / 60))
else
  echo "Time not provided, defaults to random"
fi

REMAINDER=$((DELAY_TIME_S % 60))
REMAINDER_STR=""
if [[ ! $REMAINDER -eq 0 ]]; then
  REMAINDER_STR=", $REMAINDER sec"
fi
echo "[$(date)] Wait $DELAY_TIME_M min$REMAINDER_STR before AutoMSR starts"

sleep "$DELAY_TIME_S"
echo "[$(date)] Ready to start AutoMSR"

cd "$AUTOMSR_PATH" || exit 1

possible_venvs=( ".venv" "venv" "virtualenv" )
for venv in "${possible_venvs[@]}"
do
	if [[ -f "$venv/bin/activate" ]]; then
		echo "Sourcing $venv/bin/activate"
		source "$venv/bin/activate"
		break
	fi
done

./run-now.sh || exit 1
