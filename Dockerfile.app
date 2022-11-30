FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV IN_DOCKER_CONTAINER=true

ENTRYPOINT [ "/app/run-now.sh" ]