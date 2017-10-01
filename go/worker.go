package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"time"
)

const letterBytes = "abcdef1234567890xyz"

func randStringBytes(n int) string {
	b := make([]byte, n)
	for i := range b {
		b[i] = letterBytes[rand.Intn(len(letterBytes))]
	}
	return string(b)
}

type Worker struct {
	ID        string
	DoneState int
}

// LoopUntilDone should be executed within a goroutine
func (w *Worker) LoopUntilDone(deadline time.Duration) {
	s := 0
	fmt.Printf("[%s] Initial state: %d, Desired state: %d\n", w.ID, s, w.DoneState)
	wait := time.After(deadline)
	for {
		select {
		case <-wait:
			fmt.Printf("[%s] Worker did not finish within deadline\n", w.ID)
			return
		default:
			time.Sleep(500 * time.Millisecond)
			if s == w.DoneState {
				fmt.Printf("[%s] Done! Final state: %d\n", w.ID, s)
				return
			} else {
				s++
				fmt.Printf("[%s] Still working. New state: %d\n", w.ID, s)
			}
		}
	}

}

func StartServer() {
	fmt.Println("Starting server")
	handler := func(w http.ResponseWriter, r *http.Request) {
		worker := Worker{ID: randStringBytes(5), DoneState: rand.Intn(10)}
		go worker.LoopUntilDone(4 * time.Second)
		w.Write([]byte(`Created new worker`))
	}
	http.HandleFunc("/start", handler)
	http.ListenAndServe(":8080", nil)
}

func main() {
	StartServer()
}
