# PPM Project Website

This is the source code for the PPM project website. It is built using Node.js and the Express framework with the Handlebars templating engine.

The main goal of this project was to provide The Bridges Community Trust with a method of adding articles and events to their website without the need for programming knowledge. This was achieved using:
- Markdown: New article web pages can be added by creating new plain-text/Markdown documents in the `/data/articles` directory.
- CSV: New events can be added to the events page by updating the `/data/events.csv` file.

Preview: http://tbct.didntlaugh.com/

## Pre-requisites

- Node.js [https://nodejs.org/en/]
- Docker [https://www.docker.com/] (optional)

## Run Locally

1. Clone the repository `git clone <repository-url>`
2. Run `npm install` to install dependencies
3. Run `npm run start` to start the server
4. Navigate to [http://localhost:8080](http://localhost:8080)

## Deploy with Docker

1. Clone the repository `git clone <repository-url>`
2. Run `docker build -t ppm-website .` to build the image
3. Run `docker run -d -v $(pwd)/data:/usr/src/app/data -p 8080:8080 --name ppm-website ppm-website:latest` to start the server
4. Navigate to [http://localhost:8080](http://localhost:8080)
