package main

import (
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/gorilla/context"
    "github.com/stretchr/testify/assert"
)

func TestGetRequest(t *testing.T) {

    r, _ := http.NewRequest("GET", "/test/abcd", nil)
    w := httptest.NewRecorder()

    //Hack to try to fake gorilla/mux vars
    vars := map[string]string{
        "mystring": "abcd",
    }
    context.Set(r, 0, vars)

    GetRequest(w, r)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.Equal(t, []byte("abcd"), w.Body.Bytes())
}
