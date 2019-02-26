package main

import (
	"fmt"

	"github.com/k0kubun/pp"
	"github.com/teslamotors/jsonql"
)

var jsString = `
{
  "foo": {
    "bar": 1
  },
  "baz": 2
}
`

func main() {
	parser, err := jsonql.NewStringQuery(jsString)
	if err != nil {
		fmt.Println(err)
		return
	}

	jqlExpr, err := jsonql.Parse(`foo.bar > 0`)
	if err != nil {
		fmt.Println(err)
		return
	}

	// match == nil if jqlExpr doesn't match anything in jsonString
	match, err := parser.QueryExpr(jqlExpr)
	if err != nil {
		fmt.Println(err)
		return
	}
	pp.Println(match)
}
