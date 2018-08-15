package main

import (
	"fmt"

	"github.com/natemurthy/misc/go/codegen/painkiller"
)

func main() {
	p := painkiller.Ibuprofen
	fmt.Println(p.String())
}
