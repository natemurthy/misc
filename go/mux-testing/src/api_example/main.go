package main

import (
    "encoding/json"
    "fmt"
    "net/http"

    "github.com/gorilla/mux"
)

type JsValue struct {
        Message string `json:"message"`
}

func GetRequest(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    myString := vars["mystring"]

    w.WriteHeader(http.StatusOK)
    w.Header().Set("Content-Type", "application/json; charset=UTF-8")
    json.NewEncoder(w).Encode(JsValue{Message: myString})
}

func NewRouter() *mux.Router {
    router := mux.NewRouter().StrictSlash(true)
    router.HandleFunc("/test/{mystring}", GetRequest).Name("/test/{mystring}").Methods("GET")
    return router
}

func main() {
    mainRouter := NewRouter()
    http.Handle("/", mainRouter)

    err := http.ListenAndServe(":8080", mainRouter)
    if err != nil {
        fmt.Println("Something is wrong : " + err.Error())
    }
}

