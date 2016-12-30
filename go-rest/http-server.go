package main

import (
  "net/http"
  "runtime"
  "encoding/json"
)

func main() {
  runtime.GOMAXPROCS(runtime.NumCPU())
  var m = map[string]string{
    "key": "value",
  }
  b, _ := json.Marshal(m)
  handler := func(w http.ResponseWriter, r *http.Request) {
    w.Write(b)
  }
  http.HandleFunc("/", handler)
  http.ListenAndServe(":8000", nil)
}
