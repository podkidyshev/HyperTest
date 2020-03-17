FROM python:3.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=settings.docker

RUN apt-get update && apt-get install gcc python3-dev musl-dev -y

RUN mkdir /code
WORKDIR /code

COPY ./requirements /code/requirements
RUN pip install -r /code/requirements/base.txt
RUN rm -rf /code/requirements/

COPY ./src /code/src/
COPY ./scripts /code/scripts
COPY ./docker/uwsgi.ini /code/uwsgi.ini

WORKDIR /code/src

ENTRYPOINT ["bash", "../scripts/start.sh"]