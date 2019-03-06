package main

import (
	"bufio"
	"io"
	"os"

	"github.com/k0kubun/pp"
)

// confirming line count returned from this script matches the result
// from running `wc -l` command
//
//$ go run open_file_read_lines.go
//line count 33
//
//$ wc -l open_file_read_lines.go
//   33 open_file_read_lines.go

func main() {
	f, err := os.OpenFile("open_file_read_lines.go", os.O_RDONLY, os.ModePerm)
	if err != nil {
		panic(err)
	}
	defer f.Close()

	reader := bufio.NewReader(f)

	total := 0

	for {
		if _, err := reader.ReadString('\n'); err != nil {
			if err == io.EOF {
				break
			}
			panic(err)
		}
		total++
	}

	pp.Printf("line count %v\n", total)
}
