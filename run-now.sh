echo "**********************************"
echo "******** STARTING AUTOMSR ********"
echo "**********************************"

date
TS=$(date +%F)

mkdir -p logs
venv/bin/python main.py $@ 2>&1 | tee -a "logs/automsr-$TS.log"
