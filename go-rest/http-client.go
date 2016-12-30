package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
)

func main() {
	url := "http://localhost:8000/"

	//payload := strings.NewReader("code=AUTH_CODE&client_id=CLIENT_ID&client_secret=CLIENT_SECRET&grant_type=authorization_code")
	//req, _ := http.NewRequest("POST", url, payload)
	//res, _ := http.DefaultClient.Do(req)

	res, _ := http.Get(url)
	defer res.Body.Close()
	body, _ := ioutil.ReadAll(res.Body)

	fmt.Printf("%s %s\n", res.Proto, res.Status)
	fmt.Printf("Date: %s\n", res.Header.Get("Date"))
	fmt.Printf("Content-Length: %s\n", res.Header.Get("Content-Length"))
	fmt.Printf("Content-Type: %s\n\n", res.Header.Get("Content-Type"))
	fmt.Println(string(body))
}
