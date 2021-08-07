FROM python:3.9-slim

RUN apt-get update && apt-get install -y netcat gcc libpq-dev postgresql-client

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . /usr/src/app

ENTRYPOINT ["/usr/src/app/mood_app/entrypoint.sh"]