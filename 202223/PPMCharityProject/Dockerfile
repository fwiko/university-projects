FROM node:16.15-alpine

workdir /usr/src/app
COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 8080

CMD ["npm", "run", "start"]
