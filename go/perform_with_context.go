package main

// https://siadat.github.io/post/context

import (
	"context"
	"flag"
	"fmt"
	"math/rand"
	"time"
)

var timeout int

func init() {
	flag.IntVar(&timeout, "timeout", 30, "context deadline")
	flag.Parse()
}

func Perform(ctx context.Context) error {
	target := 2
	fmt.Printf("target := %d\n", target)
	for {
		guess := rand.Intn(10)
		fmt.Printf("poll guess = %d\n", guess)
		if guess == target {
			fmt.Println("correct guess!")
			break
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(time.Second):
			// wait for 1 second
		}
	}
	return nil
}

func main() {
	parentContext := context.Background()

	d := time.Duration(timeout) * time.Second
	//ctx, _ := context.WithDeadline(parentContext, time.Now().Add(30*time.Second))
	ctx, _ := context.WithTimeout(parentContext, d)

	err := Perform(ctx)
	if err != nil {
		fmt.Println(err)
	}
}
