package main

import (
    "fmt"
    "net/http"

    "github.com/gorilla/mux"
)

func main() {
    mainRouter := mux.NewRouter().StrictSlash(true)
    mainRouter.HandleFunc("/test/{mystring}", GetRequest).Name("/test/{mystring}").Methods("GET")
    http.Handle("/", mainRouter)

    err := http.ListenAndServe(":8080", mainRouter)
    if err != nil {
        fmt.Println("Something is wrong : " + err.Error())
    }
}

func GetRequest(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    myString := vars["mystring"]

    w.WriteHeader(http.StatusOK)
    w.Header().Set("Content-Type", "text/plain")
    w.Write([]byte(myString))
}
