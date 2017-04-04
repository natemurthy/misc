package main

import (
	"fmt"
	"time"
)

func main() {
        var now = time.Now().UnixNano()
        var foo = 1491198158145595191
        fmt.Println(foo)
        foo += 1000000000
        fmt.Println(foo)
        fmt.Println(now)
	fmt.Println(now + 1000000000)
}

