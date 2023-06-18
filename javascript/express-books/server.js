require('log-timestamp')

// express framework dependencies
const express = require('express')
const app = express()

// for parsing JSON requests
const bodyParser = require('body-parser')
app.use(bodyParser.json())

// http client setup
const axios = require('axios')
const apiKey = "AIzaSyCnqAY4B3OfL7C3xgvBaXeYsMHThNZkJBY"

// database client and setup
const mysql = require('mysql2')
const con = mysql.createConnection({
  host: "localhost",
  user: "nathan",
  password: "password",
  database: "books"
})

/* Pertinent database column fields:
 *
 * title
 * books
 * booksauthors (connects books and authors)
 * authors
 * bookpublishers (connects books and publishers)
 * publishers
 *
 */

// mysql helper function for writing book info to database
function saveBooks(data) {
  con.connect(function(err) {
    if (err) throw err
    const prefix = "INSERT INTO books (title, author, publisher) VALUES ?"
    const values = data.map(book =>
      [book.title, book.author, book.publisher]
    )
    con.query(prefix, [values], function (err, result) {
      if (err) throw err
      console.log("%d rows inserted", result.affectedRows)
    })
  })
}


// mysql helper function for retrieving book info from database
function fetchBook(id, callback) {
  con.connect(function(err) {
    if (err) throw err
    const sql = `SELECT * FROM books WHERE id = ${id} LIMIT 1`
    con.query(sql, function (err, result, fields) {
      if (err) throw err
      callback(result)
    })
  })
}


// endpoint for creating new book entries from Google given an author
app.post('/api/books', (req, res) => {
  const query = req.body.author
  console.log("search query = '%s'", query)
  const url = "https://www.googleapis.com/books/v1/volumes?q="+ query + "&key=" + apiKey

  axios.get(url).then(gbooks => { 
    // gbooks.data will hold 10 items by default and so
    // bookInfo will have a size of 10 as well
    const bookInfo = gbooks.data.items.map(i => i.volumeInfo).map(info => (
      {
        title: info.title,
        author: info.authors[0],
        publisher: info.publisher
      }
    ))
    saveBooks(bookInfo)
    res.send(JSON.stringify(bookInfo))
  })
})


// endpoint for reading existing book entries from the database
app.get('/api/books/:id', (req, res) => {
  res.setHeader('Content-Type', 'application/json')
  fetchBook(req.params.id, (book) => {
    res.send(JSON.stringify(book))
  })
})


// launch the server
const port = process.env.PORT || 3000
const server = app.listen(port, () => {
  console.log("listening on port %s...", server.address().port)
})
