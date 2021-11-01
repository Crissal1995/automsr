echo
echo "**********************************"
echo "****** STARTING RUN_AUTOMSR ******"
echo "**********************************"

date
TS=$(date +%F)

cd $HOME/auto_msrewards
mkdir -p logs
venv/bin/python main.py $@ 2>&1 | tee -a "logs/automsr-$TS.log"
