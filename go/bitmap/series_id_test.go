package main

import (
	"math/rand"
	"testing"
)

func TestSeriesID(t *testing.T) {
	types := []FieldType{
		Integer,
		Float,
		Boolean,
		String,
		Unsigned,
	}

	for i := 0; i < 1000000; i++ {
		id := NewSeriesID(uint64(rand.Int31()))
		for _, typ := range types {
			typed := id.WithType(typ)
			if got := typed.Type(); got != typ {
				t.Fatalf("wanted: %v got: %v", typ, got)
			}
			if got := typed.SeriesID(); id != got {
				t.Fatalf("wanted: %016x got: %016x", id, got)
			}
		}
	}
}
