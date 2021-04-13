FROM python:3.8-slim-buster

WORKDIR /app

# crontab
RUN apt update && apt -y install cron

# copy reqs and install them
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# copy files
COPY . .

# copy crontab file
COPY daily-cron /etc/cron.d/daily-cron
RUN chmod 0644 /etc/cron.d/daily-cron
RUN crontab /etc/cron.d/daily-cron
RUN touch /var/log/cron.log

# entry point script
ENTRYPOINT ["/app/entry.sh"]
