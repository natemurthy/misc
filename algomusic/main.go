package main

// Borrowed from: https://github.com/hajimehoshi/go-mp3/blob/master/example/main.go

import (
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"

	"github.com/hajimehoshi/go-mp3"
	"github.com/hajimehoshi/oto"
)

var (
	input = flag.String("input", "input.mp3", "name of mp3 file")
)

func play(f *os.File) error {

	d, err := mp3.NewDecoder(f)
	if err != nil {
		return err
	}
	defer d.Close()

	p, err := oto.NewPlayer(d.SampleRate(), 2, 2, 8192)
	if err != nil {
		return err
	}
	defer p.Close()

	log.Printf("Length: %d[bytes]\n", d.Length())

	if _, err := io.Copy(p, d); err != nil {
		return err
	}

	return nil
}

func main() {
	flag.Parse()

	f, err := os.Open(*input)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	go func() {
		for i := 47; i < 55000; i = i + 50 {
			window := fmt.Sprintf("%d,%dp", i, i+50)
			c1 := exec.Command("xxd", "-b", "-c", "9", *input)
			c2 := exec.Command("sed", "-n", window)
			c2.Stdin, _ = c1.StdoutPipe()
			c2.Stdout = os.Stdout
			_ = c2.Start()
			_ = c1.Run()
			_ = c2.Wait()
		}
	}()

	if err := play(f); err != nil {
		log.Fatal(err)
	}
}
