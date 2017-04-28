// following slides from https://tour.golang.org/concurrency/11

package main

import (
    "fmt"
    "math/rand"
    "time"
)

func main() {
    joe := boring("joe")
    ann := boring("ann")
    fmt.Println("I'm listening.")
    for i := 0; i < 5; i++ {
        fmt.Printf("%q\n", <-joe)
        fmt.Printf("%q\n", <-ann)
    }
    fmt.Println("You're boring; I'm leaving.")
}

func boring(msg string) <-chan string {
    c := make(chan string)
    go func() {
        for i := 0; ; i++ {
            c <- fmt.Sprintf("%s %d", msg, i)
            time.Sleep(time.Duration(rand.Intn(1e3)) * time.Millisecond)
        }
    }()
    return c
}
