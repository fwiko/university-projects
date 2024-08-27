const express = require('express');
const marked = require('marked');
const markedImages = require('marked-images');
const fs = require('fs');
const csv = require('csv-parse');

marked.use(markedImages())

const router = express.Router();

const getSortedArticles = async (dir) => {
    const files = await fs.promises.readdir(dir);

    const sorted = files
        .map(fileName => ({
            name: fileName,
            time: fs.statSync(`${dir}/${fileName}`).mtime.getTime(),
        }))
        .sort((a, b) => b.time - a.time)

    return sorted;
};

const getPreviewArticles = async (dir) => {
    const previewArticles = [];
    const sortedArticles = await getSortedArticles(dir);

    for (let i = 0; i < sortedArticles.length; i++) {
        const articleFilePath = `${dir}/${sortedArticles[i].name}`;
        const articleContents = fs.readFileSync(articleFilePath, 'utf8');

        if (articleContents.trim().length == 0) {
            console.log(`Article ${sortedArticles[i].name} is empty, skipping...`);
            continue;
        }

        const articlePreview = marked.lexer(articleContents).filter(token => token.type === 'paragraph' && token.text.substring(0, 2) != "![")[0].text.trim().substring(0, 75) + "...";
        previewArticles.push({
            name: sortedArticles[i].name.split('.')[0].split('-').join(' '),
            content: articlePreview,
            link: sortedArticles[i].name.split('.')[0],
            time: new Date(sortedArticles[i].time).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
        });
    }

    return previewArticles;
};

const getUpcomingEvents = async () => {
    const eventsFilePath = `./data/events.csv`;
    const events = [];
    csv.parse(fs.readFileSync(eventsFilePath, 'utf8'), (err, data) => {
        if (err) {
            console.log(err);
        }
        else {
            for (let i = 1; i < data.length; i++) {
                events.push({
                    name: data[i][0],
                    location: data[i][1],
                    time: data[i][2],
                });
            }
        }
    });
    return events;
};

// Home Page
router.get('/', async (req, res) => {
    const previewArticles = (await getPreviewArticles('./data/articles')).slice(0, 4);
    return res.render('home', { title: 'The Bridges Community Trust', previewArticles });
});

// About Page
router.get('/about', async (req, res) => {// about page
    return res.render('about', { title: 'About the Trust' });
});

// Services Page
router.get('/services', async (req, res) => {// services page
    return res.render('services', { title: 'Our Services' });
});

// Employment Support Page
router.get('/employment-support', async (req, res) => {
    return res.render('employment-support', { title: 'Employment Support' });
});

// Contact Page
router.get('/contact', async (req, res) => {
    return res.render('contact', { title: 'Contact Us' });
});

router.post('/contact', async (req, res) => {
    const { name, phone, message } = req.body;
    console.log("New email: " + name, phone, message); // pretend email sent - no where to send it to currently (theoretically this would be extended to send an email to the bridges community trust email)
    return res.render('contact', { title: 'Contact Us', message: 'Thank you for your message, we will be in touch shortly.' });
});

// Newsletter Page
router.get('/newsletter', async (req, res) => {
    return res.render('newsletter', { title: 'Newsletter' });
});

// News Page
router.get('/news', async (req, res) => {
    const previewArticles = await getPreviewArticles('./data/articles');
    return res.render('news', { title: 'News', previewArticles });
});

// News Page(s)
router.get('/news/*', async (req, res) => {
    const articleName = req.params[0]; // get the news article name from the url
    const articleFilePath = `./data/articles/${articleName}.md`;

    if (!fs.existsSync(articleFilePath)) { // if the file doesn't exist
        return res.send('404: Article not found: ' + articleFilePath);
    }

    const articleContent = fs.readFileSync(articleFilePath, 'utf8'); // read the file

    return res.render('article', {
        title: articleName.split('-').join(' '),
        content: marked.parse(articleContent)
    })
});

// Events Page
router.get('/events', async (req, res) => {
    return res.render('events', { title: 'Upcoming Events', events: await getUpcomingEvents() });
});

// Catch all and redirect to home page
router.get('*', async (req, res) => {
    res.redirect('/');
});


module.exports = router;