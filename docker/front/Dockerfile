FROM node:12.8.1-alpine as build

RUN mkdir /app
WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

COPY ./front/package-lock.json /app/package-lock.json
RUN npm install --silent
RUN npm install react-scripts@3.0.1 -g --silent

RUN ls

COPY ./front/public /app/public/
COPY ./front/src /app/src

RUN npm run build

RUN rm -rf /app/src
RUN rm -rf /app/public
