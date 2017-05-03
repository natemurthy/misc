package main

import "fmt"

var currentID chan int
var todos Todos

// Give us some seed data
func init() {
	currentID = make(chan int, 1)
	currentID <- 0
	todos = make(map[int]Todo)
	RepoCreateTodo(Todo{Name: "Write presentation", Completed: true})
	RepoCreateTodo(Todo{Name: "Host meetup", Completed: true})
}

// RepoFindTodo returns a todo record with the given ID
func RepoFindTodo(id int) (Todo, bool) {
	t, present := todos[id]
	return t, present
}

// RepoCreateTodo creates and returns a new todo record
func RepoCreateTodo(t Todo) Todo {
	currID := <-currentID
	currID++
	t.ID = currID
	currentID <- currID
	todos[currID] = t
	return t
}

// RepoDestroyTodo delete todo record with the given ID
func RepoDestroyTodo(id int) error {
	if _, present := todos[id]; present {
		delete(todos, id)
		return nil
	}
	return fmt.Errorf("Could not find Todo with ID of %d to delete", id)
}
