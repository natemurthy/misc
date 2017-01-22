package main

import (
	"fmt"
	"sync"
	"time"
)

var wg sync.WaitGroup

const COUNT = 80000000

func Countdown(n int) {
	defer wg.Done()
	for n > 0 {
		n -= 1
	}
	//fmt.Println(n)
}

func main() {
	start := time.Now()
	wg.Add(2)
	go Countdown(COUNT/2)
	go Countdown(COUNT/2)
	wg.Wait()
	elapsed := time.Since(start)
	fmt.Println(elapsed)
}
