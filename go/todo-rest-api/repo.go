package main

import (
	"fmt"
)

var currentID chan int
var todos Todos

// Give us some seed data
func init() {
	currentID = make(chan int, 1)
	currentID <- 0

	RepoCreateTodo(Todo{Name: "Write presentation", Completed: true})
	RepoCreateTodo(Todo{Name: "Host meetup", Completed: true})
}

// RepoFindTodo returns a todo record with the given ID
func RepoFindTodo(id int) Todo {
	for _, t := range todos {
		if t.ID == id {
			return t
		}
	}
	// return empty Todo if not found
	return Todo{}
}

// RepoCreateTodo creates and returns a new todo record
func RepoCreateTodo(t Todo) Todo {
	currID := <-currentID
	currID++
	t.ID = currID
	currentID <- currID
	todos = append(todos, t)
	return t
}

// RepoDestroyTodo delete todo record with the given ID
func RepoDestroyTodo(id int) error {
	for i, t := range todos {
		if t.ID == id {
			todos = append(todos[:i], todos[i+1:]...)
			return nil
		}
	}
	return fmt.Errorf("Could not find Todo with id of %d to delete", id)
}
