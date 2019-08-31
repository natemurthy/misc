package main

import (
	"fmt"

	"github.com/anthonynsimon/bild/adjust"
	"github.com/anthonynsimon/bild/imgio"
)

func main() {
	img, err := imgio.Open("input.png")
	if err != nil {
		fmt.Println(err)
		return
	}

	result := adjust.Saturation(img, 0.8)

	if err := imgio.Save("output.png", result, imgio.PNGEncoder()); err != nil {
		fmt.Println(err)
		return
	}
}
