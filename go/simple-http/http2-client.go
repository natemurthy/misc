package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"net/http"

	"golang.org/x/net/http2"
)

func main() {
	url := flag.String("url", "https://http2.golang.org/", "The URL of the desired resource to fetch")
	flag.Parse()

	client := http.Client{
		Transport: new(http2.Transport),
	}

	res, err := client.Get(*url)

	if err != nil {
		fmt.Println("An error occurred:", err.Error())
	} else {
		defer res.Body.Close()
		body, _ := ioutil.ReadAll(res.Body)

		fmt.Printf("%s %s\n", res.Proto, res.Status)
		fmt.Printf("Date: %s\n", res.Header.Get("Date"))
		fmt.Printf("Content-Length: %s\n", res.Header.Get("Content-Length"))
		fmt.Printf("Content-Type: %s\n\n", res.Header.Get("Content-Type"))
		fmt.Println(string(body))
	}

}
