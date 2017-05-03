package main

import "time"

// Todo defines an entity for each todo list record
type Todo struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	Completed bool      `json:"completed"`
	Due       time.Time `json:"due"`
}

// Todos is a map of todo structs
type Todos map[int]Todo

func (todos Todos) Values() []Todo {
	values := []Todo{}
	for _, v := range todos {
		values = append(values, v)
	}
	return values
}
