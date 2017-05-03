package main

import (
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"net/http"
	"strconv"

	"github.com/gorilla/mux"
)

type jsonErr struct {
	Message string `json:"message"`
}

// Index prints welcome page
func Index(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "Welcome!\n")
}

// TodoIndex gets all todo recods from repo
func TodoIndex(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json; charset=UTF-8")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(todos.Values())
}

// TodoShow gets individual todo record by ID from repo
func TodoShow(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	var todoID int
	var err error
	if todoID, err = strconv.Atoi(vars["todoId"]); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(jsonErr{Message: "Todo.ID must be an integer"})
		return
	}
	if todo, present := RepoFindTodo(todoID); present {
		w.Header().Set("Content-Type", "application/json; charset=UTF-8")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(todo)
	} else {
		w.Header().Set("Content-Type", "application/json; charset=UTF-8")
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(jsonErr{Message: "Not Found"})
	}
}

// TodoCreate saves new todo record to repo
func TodoCreate(w http.ResponseWriter, r *http.Request) {
	var todo Todo
	body, err := ioutil.ReadAll(io.LimitReader(r.Body, 1048576))
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(jsonErr{Message: "Request body too large (>1MB)"})
		return
	}
	if err := r.Body.Close(); err != nil {
		panic(err)
	}
	if err := json.Unmarshal(body, &todo); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(jsonErr{Message: "Unable to parse JSON"})
		return
	}

	t := RepoCreateTodo(todo)
	w.Header().Set("Content-Type", "application/json; charset=UTF-8")
	w.WriteHeader(http.StatusCreated)
	if err := json.NewEncoder(w).Encode(t); err != nil {
		panic(err)
	}
}

// TodoDelete removes todo record from repo
func TodoDelete(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	var todoID int
	var err error
	if todoID, err = strconv.Atoi(vars["todoId"]); err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(jsonErr{Message: "Todo.ID must be an integer"})
		return
	}
	if err := RepoDestroyTodo(todoID); err != nil {
		w.WriteHeader(http.StatusNotFound)
		json.NewEncoder(w).Encode(jsonErr{Message: err.Error()})
	} else {
		w.WriteHeader(http.StatusNoContent)
	}
}
