FROM node:12.8.1-alpine

RUN mkdir -p /app
WORKDIR /app

ENV PATH /app/node_modules/.bin:$PATH

COPY ./package.json /app/

RUN npm install --silent --no-optional --only=prod --no-audit --no-cache
RUN npm install react-scripts@3.4.0 -g --silent

COPY public /app/public/
COPY src /app/src

CMD ["npm", "start"]
