FROM node:12.8.1-alpine as build

RUN mkdir -p /app/build
WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

COPY ./front/package*.json /app/

RUN npm install --silent --no-optional --only=prod --no-audit --no-cache

COPY ./front/public /app/public/
COPY ./front/src /app/src

ENTRYPOINT ["sh", "-c", "npm run build"]
