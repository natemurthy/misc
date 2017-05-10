package main

import (
    "encoding/json"
    "fmt"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/stretchr/testify/assert"
)

func TestGetTodos(t *testing.T) {
    r, _ := http.NewRequest("GET", "/todos", nil)
    w := httptest.NewRecorder()
    NewRouter().ServeHTTP(w, r)

    var resp []Todo
    json.Unmarshal(w.Body.Bytes(), &resp)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.Equal(t, len(resp),     2)
}
