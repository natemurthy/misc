package main

import (
	"database/sql"
	"encoding/json"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"github.com/gorilla/mux"
)

const apiKey = "AIzaSyCnqAY4B3OfL7C3xgvBaXeYsMHThNZkJBY"

// JsError is an error response message
type JsError struct {
	Message string `json:"message"`
}

// Author for search query
type Author struct {
	Author string `json:"author"`
}

// GoogleBooks JSON response
type GoogleBooks struct {
	Items []BookItem `json:"items"`
}

// BookItem from Google Books API
type BookItem struct {
	VolumeInfo VolumeInfo `json:"volumeInfo"`
}

// VolumeInfo from Google Books API
type VolumeInfo struct {
	Title     string   `json:"title"`
	Authors   []string `json:"authors"`
	Publisher string   `json:"publisher"`
}

// Book object for saving and fetching books to database
type Book struct {
	ID        int    `json:"id"`
	Title     string `json:"title"`
	Author    string `json:"author"`
	Publisher string `json:"publisher"`
}

var db *sql.DB

func init() {
	var err error
	db, err = sql.Open("mysql", "nathan:password@/books")
	if err != nil {
		panic(err)
	}
}

func saveBooks(db *sql.DB, gbooks GoogleBooks) {
	query := "INSERT INTO books(title, author, publisher) VALUES "
	vals := []interface{}{}

	for _, item := range gbooks.Items {
		query += "(?, ?, ?),"
		title := item.VolumeInfo.Title
		author := item.VolumeInfo.Authors[0]
		publisher := item.VolumeInfo.Publisher
		vals = append(vals, title, author, publisher)
	}
	query = strings.TrimSuffix(query, ",")
	stmt, _ := db.Prepare(query)
	res, _ := stmt.Exec(vals...)
	n, _ := res.RowsAffected()
	log.Printf("%d rows inserted", n)
}

func fetchBook(db *sql.DB, id int) Book {
	var book Book
	query := `select * from books where id = ? limit 1`
	stmt, err := db.Prepare(query)
	if err != nil {
		log.Fatal(err)
	}
	row := stmt.QueryRow(id)
	if err != nil {
		log.Fatal(err)
	}
	row.Scan(&book.ID, &book.Title, &book.Author, &book.Publisher)
	defer stmt.Close()
	return book
}

// GetBook reads a book from the database and marshals it as JSON
func GetBook(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	var bookID int
	var err error
	if bookID, err = strconv.Atoi(vars["id"]); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(JsError{Message: "api/books/id must be an integer"})
		return
	}
	fetchBook(db, bookID)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(fetchBook(db, bookID))
}

// PostBooks pulls books from the Googe API based on author and writes it
// to the database
func PostBooks(w http.ResponseWriter, r *http.Request) {
	var author Author
	authorBody, err := ioutil.ReadAll(io.LimitReader(r.Body, 1048576))

	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(JsError{Message: "Request body too large (>1MB)"})
		return
	}

	if err := r.Body.Close(); err != nil {
		log.Fatal(err)
	}

	if err := json.Unmarshal(authorBody, &author); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(JsError{Message: "Unable to parse JSON"})
		return
	}

	query := url.QueryEscape(author.Author)
	url := "https://www.googleapis.com/books/v1/volumes?q=" + query + "&key=" + apiKey
	resp, err := http.Get(url)
	if err != nil {
		log.Fatal(err)
	}
	gbooksBody, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}

	var gbooks GoogleBooks
	if err := json.Unmarshal(gbooksBody, &gbooks); err != nil {
		log.Fatal(err)
	}

	saveBooks(db, gbooks)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(gbooks)
}

// Route defines mappings between HTTP paths and handlers
type Route struct {
	Name        string
	Method      string
	Pattern     string
	HandlerFunc http.HandlerFunc
}

// Routes is an array of route structs
type Routes []Route

var routes = Routes{
	Route{
		"GetBook",
		"GET",
		"/api/books/{id}",
		GetBook,
	},
	Route{
		"PostBooks",
		"POST",
		"/api/books",
		PostBooks,
	},
}

// Logger wraps a handler for logging HTTP requests
func Logger(inner http.Handler, name string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()

		inner.ServeHTTP(w, r)

		log.Printf(
			"%s %s %s %s",
			r.Method,
			r.RequestURI,
			name,
			time.Since(start),
		)
	})
}

// NewRouter returns a gorilla/mux router with handlers attached
func NewRouter() *mux.Router {
	router := mux.NewRouter().StrictSlash(true)
	for _, route := range routes {
		var handler http.Handler

		handler = route.HandlerFunc
		handler = Logger(handler, route.Name)

		router.
			Methods(route.Method).
			Path(route.Pattern).
			Name(route.Name).
			Handler(handler)

	}
	return router
}

func main() {
	router := NewRouter()
	log.Fatal(http.ListenAndServe(":3000", router))
}
