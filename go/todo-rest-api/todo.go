package main

import "time"

// Todo defines an entity for each todo list record
type Todo struct {
	ID        int       `json:"id"`
	Name      string    `json:"name"`
	Completed bool      `json:"completed"`
	Due       time.Time `json:"due"`
}

// Todos is an array of todo structs
type Todos []Todo
