package main

import (
	"errors"
	"fmt"
	"math/rand"
	"time"
)

type wrapper struct {
	i int
	s string
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

func main() {
	i := registerScema("mahal", "kita")
	fmt.Println(time.Now().Unix(), i)
}

func registerScema(subj string, sch string) int {

	r1 := new(wrapper)
	r2 := new(wrapper)

	task := async.Scatter(
		func() error { return isRegistered(subj, sch, r1).Error() },
		func() error { return isRegistered(sch, subj, r2).Error() },
	)

	task.Gather()
	fmt.Println(r1.i, r1.s, r2.i, r2.s)

	return r1.i + r2.i
}

func isRegistered(subj string, sch string, w *wrapper) async.Result {
	return async.NewResult(func() error {
		i := rand.Intn(len(subj) + len(sch))
		fmt.Println(time.Now().Unix(), i)
		w.i = i

		time.Sleep(time.Duration(i) * time.Second)

		if i%2 == 0 {

			w.s = "bad"
			return errors.New(w.s)
		}
		w.s = "good"
		return nil
	})
}
