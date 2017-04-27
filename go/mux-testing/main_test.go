package main

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/stretchr/testify/assert"
)

// see http://stackoverflow.com/questions/34435185/unit-testing-for-functions-that-use-gorilla-mux-url-parameters
func TestGetRequest(t *testing.T) {

    r, _ := http.NewRequest("GET", "/test/abcd", nil)
    w := httptest.NewRecorder()

    NewRouter().ServeHTTP(w, r)

    var resp JsValue
    json.Unmarshal(w.Body.Bytes(), &resp)
    expect := JsValue{Message: "abcd"}

    assert.Equal(t, http.StatusOK, w.Code)
    assert.Equal(t, expect,        resp  )
}
