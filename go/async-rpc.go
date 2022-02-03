package main

import (
	"fmt"
	"math/rand"
	"time"
)

func rpcOne() int32 {
	time.Sleep(time.Second * 3)
	return rand.Int31n(100)
}

func rpcTwo() int32 {
	time.Sleep(time.Second * 3)
	return rand.Int31n(100)
}

func tasks() int32 {
	r := make(chan int32)
	s := make(chan int32)

	go func() {
		defer close(r)
		r <- rpcOne()
	}()

	go func() {
		defer close(s)
		s <- rpcTwo()
	}()

	return <-r + <-s
}

func main() {
	// takes 3 seconds in total
	fmt.Println(tasks())
}
