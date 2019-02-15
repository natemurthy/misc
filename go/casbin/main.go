package main

import (
	"fmt"
	"os"

	"github.com/casbin/casbin"
)

func main() {
	e := casbin.NewEnforcer("model.conf", "policy.csv")

	args := os.Args
	if len(args[1:]) != 3 {
		fmt.Println("usage: go run main.go [sub] [obj] [act]")
		os.Exit(1)
	}
	sub := args[1] // the group that wants to access a resource.
	obj := args[2] // the resource that is going to be accessed.
	act := args[3] // the operation that the user performs on the resource.

	if e.Enforce(sub, obj, act) == true {
		fmt.Println("allowed")
	} else {
		fmt.Println("denied")
	}

}
