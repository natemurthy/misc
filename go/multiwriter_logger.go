package main

import (
	"io"
	"log"
	"os"
)

func main() {
	f, _ := os.OpenFile("/tmp/app.log", os.O_CREATE|os.O_APPEND|os.O_RDWR, 0666)
	mw := io.MultiWriter(os.Stdout, f)
	log.SetOutput(mw)

	log.Println("test log write")
}
