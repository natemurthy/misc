package main

import (
	"fmt"
	"time"
)

func main() {
	// incrementing timestamp
        var now = time.Now().UnixNano()
        var foo = 1491198158145595191
        fmt.Println(foo)
        foo += 1000000000
        fmt.Println(foo)
        fmt.Println(now)
	fmt.Println(now + 1000000000)
	
	//render
        dtStr := now.Format(time.RFC3339)
        fmt.Println(dtStr)

        //parse
        s := dtStr // "2017-07-18T18:50:20.123Z"
        dtTime, err := time.Parse(time.RFC3339, s)
        if err != nil {
                fmt.Println(err)
                return
        } else {
                fmt.Println(dtTime.UnixNano())
        }
}

