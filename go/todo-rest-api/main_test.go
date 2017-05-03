package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/stretchr/testify/assert"
)

// see http://stackoverflow.com/questions/34435185/unit-testing-for-functions-that-use-gorilla-mux-url-parameters
func TestGetRequest(t *testing.T) {

    r, _ := http.NewRequest("GET", "/todos", nil)
    w := httptest.NewRecorder()

    NewRouter().ServeHTTP(w, r)

    var resp []Todo
    json.Unmarshal(w.Body.Bytes(), &resp)
    //expect := JsValue{Message: "abcd"}
    fmt.Println(resp)
    assert.Equal(t, http.StatusOK, w.Code)
    assert.Equal(t, len(resp),     2)
    //assert.Equal(t, expect,        resp  )
}
