package main

import (
	"testing"
	"time"
)

//goos: darwin
//goarch: amd64
//BenchmarkStringToTimestamp-8   	   5000000	       267    ns/op
//BenchmarkUnixToTimestamp-8     	2000000000	         0.31 ns/op

func BenchmarkStringToTimestamp(b *testing.B) {
	t := "2018-08-08T21:44:20.342661023Z"
	for n := 0; n < b.N; n++ {
		time.Parse(time.RFC3339, t)
	}
}

func BenchmarkUnixToTimestamp(b *testing.B) {
	t := int64(1533768203)
	for n := 0; n < b.N; n++ {
		time.Unix(t, 0)
	}
}
