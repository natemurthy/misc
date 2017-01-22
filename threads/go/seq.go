package main

import (
	"fmt"
	"time"
)

const COUNT = 80000000

func Countdown(n int) {
	for n > 0 {
		n -= 1
	}
}

func main() {
	start := time.Now()
	Countdown(COUNT)
	elapsed := time.Since(start)
	fmt.Println(elapsed)
}
