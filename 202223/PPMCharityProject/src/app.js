const path = require('path');
const express = require('express');
const sass = require('node-sass-middleware');
const { engine } = require('express-handlebars');

// import the server config file
const config = require('../data/config');

const app = express();

app.use(
    sass({
        src: path.join(__dirname, './sass'),
        dest: path.join(__dirname, '../public/styles'),

        outputStyle: 'compressed',
        prefix: '/styles',
    })
)

app.use(express.urlencoded({
    extended: false
}));
app.use(express.json());

app.use(express.static(path.join(__dirname, '../public')));

// set the engine to use handlebars templating
app.engine('handlebars', engine({
    defaultLayout: 'main',
}));
app.set('view engine', 'handlebars');

// set the routes with the routes folder as the base
app.use('/', require('./routes'));

app.listen(config.server.port, config.server.host, () => console.log(`Server started on port ${config.server.port}`));
