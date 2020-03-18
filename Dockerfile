FROM python:3.7-alpine

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=settings.docker

RUN apk update \
    && apk add --no-cache postgresql-dev gcc python3-dev musl-dev libc-dev linux-headers jpeg-dev zlib-dev

RUN mkdir /code
WORKDIR /code

COPY ./requirements /code/requirements
RUN pip install -r /code/requirements/base.txt
RUN rm -rf /code/requirements/

COPY ./src /code/src/
COPY ./scripts /code/scripts
COPY ./docker/uwsgi.ini /code/uwsgi.ini

WORKDIR /code/src

RUN mkdir -p /code/media
RUN mkdir -p /code/static

ENTRYPOINT ["/bin/sh", "-c", "../scripts/start.sh"]