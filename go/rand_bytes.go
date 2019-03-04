package main

import (
	"fmt"
	"math/rand"
	"time"
)

// reference: https://medium.com/@kpbird/golang-generate-fixed-size-random-string-dd6dbd5e63c0

const (
	letterBytes   = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	letterIdxBits = 6                    // 6 bits to represent a letter index
	letterIdxMask = 1<<letterIdxBits - 1 // All 1-bits, as many as letterIdxBits
	letterIdxMax  = 63 / letterIdxBits   // # of letter indices fitting in 63 bits
)

func randBytes(n int) []byte {
	// rand.NewSource is not thread-safe
	// see https://github.com/golang/go/issues/21099#issuecomment-317973851
	src := rand.NewSource(time.Now().UnixNano())

	b := make([]byte, n)

	// A src.Int63() generates 63 random bits, enough for letterIdxMax characters!
	for i, cache, remain := n-1, src.Int63(), letterIdxMax; i >= 0; {
		if remain == 0 {
			cache, remain = src.Int63(), letterIdxMax
		}
		if idx := int(cache & letterIdxMask); idx < len(letterBytes) {
			b[i] = letterBytes[idx]
			i--
		}
		cache >>= letterIdxBits
		remain--
	}
	return b
}

func main() {
	fmt.Println(string(randBytes(10)))
}
