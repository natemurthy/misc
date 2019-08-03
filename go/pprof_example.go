package main

import (
	"fmt"
	"log"
	"net/http"
	_ "net/http/pprof"
	"sync"
	"time"
)

// endpoint availabe on: localhost:6060/debug/pprof

func main() {
	// we need a webserver to get the pprof webserver
	go func() {
		log.Println(http.ListenAndServe("localhost:6060", nil))
	}()
	fmt.Println("hello world")
	var wg sync.WaitGroup
	wg.Add(1)
	go profiledFunc(wg)
	wg.Wait()
}

func profiledFunc(wg sync.WaitGroup) {
	defer wg.Done()
	for i := 0; i < 10000000; i++ {
		if (i % 100000) == 0 {
			time.Sleep(500 * time.Millisecond)
		}
	}
}
