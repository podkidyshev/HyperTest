FROM node:12.8.1-alpine as build

RUN mkdir /app
WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

COPY ./front/package_lock.json /app/package_lock.json
RUN npm install --silent

COPY ./front/ /app/

RUN npm run build
