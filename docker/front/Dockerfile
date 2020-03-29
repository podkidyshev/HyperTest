FROM node:12.8.1-alpine as build

RUN mkdir -p /app/build
WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

COPY ./package*.json /app/

RUN npm install --silent --no-optional --only=prod --no-audit --no-cache

COPY public /app/public/
COPY src /app/src
