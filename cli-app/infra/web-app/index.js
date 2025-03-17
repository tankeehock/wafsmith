// app.js
const express = require('express');
const app = express();
let port = process.env.PORT || 3000;

// Middleware to parse URL-encoded form data
app.use(express.urlencoded({ extended: true }));


// Serve static files from the "public" directory
app.use(express.static('public'));

// Route for the root URL ("/")
app.get('/', (req, res) => {
    res.send('Hello, World!');
});

app.post('/', (req, res) => {
    res.send('Hello, World!');
});

app.get('/debug', (req, res) => {
    res.send(req.query);
});

app.post('/debug', (req, res) => {
    res.send(req.body);
});



// Route for "/about"
app.get('/about', (req, res) => {
    res.send('This is the about page for the test site!');
});

app.get('/ping', (req, res) => {
    res.send('This is the about page.');
});

app.post('/ping', (req, res) => {
    res.send('pong');
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});