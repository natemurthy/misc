package main

import (
    "bytes"
    "encoding/json"
    "math/rand"
    "net/http"
    "net/http/httptest"
    "testing"

    "github.com/stretchr/testify/assert"
)

func TestGetAllTodos(t *testing.T) {
    r, _ := http.NewRequest("GET", "/todos", nil)
    w := httptest.NewRecorder()
    NewRouter().ServeHTTP(w, r)

    var resp []Todo
    json.Unmarshal(w.Body.Bytes(), &resp)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.Equal(t, len(resp),     2)
}

func TestGetTodoByID(t *testing.T) {
    // OK
    r1, _ := http.NewRequest("GET", "/todos/1", nil)
    w1 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w1,r1)

    var resp1 Todo
    json.Unmarshal(w1.Body.Bytes(), &resp1)

    assert.Equal(t, http.StatusOK, w1.Code )
    assert.Equal(t, 1, resp1.ID)

    // Not Found
    r2, _ := http.NewRequest("GET", "/todos/88", nil)
    w2 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w2,r2)

    assert.Equal(t, http.StatusNotFound, w2.Code)

    // Bad Request
    r3, _ := http.NewRequest("GET", "/todos/invalid1", nil)
    w3 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w3,r3)

    assert.Equal(t, http.StatusBadRequest, w3.Code)
}

func TestPostTodo(t *testing.T) {
    // OK
    var b1 = []byte(`{"name":"foo", "completed": false}`)
    r1, _ := http.NewRequest("POST", "/todos", bytes.NewBuffer(b1))
    w1 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w1,r1)

    var resp1 Todo
    json.Unmarshal(w1.Body.Bytes(), &resp1)

    assert.Equal(t, http.StatusCreated, w1.Code)
    assert.Equal(t, "foo", resp1.Name)

    // Too large a request
    var b2 = make([]byte, 2048577)
    rand.Read(b2)
    r2, _ := http.NewRequest("POST", "/todos", bytes.NewBuffer(b2))
    w2 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w2,r2)

    var resp2 JsError
    json.Unmarshal(w2.Body.Bytes(), &resp2)
    assert.Equal(t, http.StatusBadRequest, w2.Code)
    //assert.Equal(t, "Request body too large (>1MB)", resp2.Message)

    // Bad request, invalid JSON
    var b3 = make([]byte, 4)
    rand.Read(b3)
    r3, _ := http.NewRequest("POST", "/todos", bytes.NewBuffer(b3))
    w3 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w3,r3)

    var resp3 JsError
    json.Unmarshal(w3.Body.Bytes(), &resp3)
    assert.Equal(t, http.StatusBadRequest, w3.Code)
    assert.Equal(t, "Unable to parse JSON", resp3.Message)
}

func TestDeleteTodo(t *testing.T) {
    // no content
    r1, _ := http.NewRequest("DELETE", "/todos/1", nil)
    w1 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w1,r1)

    assert.Equal(t, http.StatusNoContent, w1.Code)

    // bad request
    r2, _ := http.NewRequest("DELETE", "/todos/invalid", nil)
    w2 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w2,r2)

    assert.Equal(t, http.StatusBadRequest, w2.Code)

    // not found
    r3, _ := http.NewRequest("DELETE", "/todos/888", nil)
    w3 := httptest.NewRecorder()
    NewRouter().ServeHTTP(w3,r3)

    assert.Equal(t, http.StatusNotFound, w3.Code)
}
