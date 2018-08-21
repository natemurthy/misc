package main

//go:generate go run avro-gen.go

type Foo struct {
	ID         uint64 `json:"id"`
	Name       string `json:"name"`
	QuickAlias string `json:"quick_alias"`
}
