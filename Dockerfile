FROM python:3.7-slim

ENV PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=settings.docker

RUN mkdir /code
WORKDIR /code

COPY ./requirements /code/requirements
RUN pip install -r /code/requirements/base.txt
RUN rm -rf /code/requirements/

COPY ./src /code/src/
COPY ./scripts /code/scripts

WORKDIR /code/src

ENTRYPOINT ["bash", "../scripts/start.sh"]