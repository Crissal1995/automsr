echo "**********************************"
echo "******** STARTING AUTOMSR ********"
echo "**********************************"

date
TS=$(date +%F)

# sleep at most 15 minutes
MAX_TIME=$(expr 15 \* 60)
RAND_NUM=$(awk -v min=0 -v max=$MAX_TIME 'BEGIN{srand(); print int(min+rand()*(max-min+1))}')

echo "Sleep $RAND_NUM seconds..."
sleep $RAND_NUM
echo "Running automsr!"
date

mkdir -p logs
venv/bin/python main.py $@ 2>&1 | tee -a "logs/automsr-$TS.log"
