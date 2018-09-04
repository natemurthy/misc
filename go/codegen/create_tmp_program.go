package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"sync"
)

var (
	models = []string{"pedigree", "message", "foo"}
)

func createProgram(model string) {
	programStr := `
	package main

	import (
		"fmt"
		"os"
	)

	func main() {
		fmt.Println("tmp program")
		fmt.Println(os.Getwd())
		fmt.Println(os.Args[0])
	}
	`
	content := []byte(programStr)
	dir, err := ioutil.TempDir("", "example")
	if err != nil {
		log.Fatal(err)
	}

	defer os.RemoveAll(dir)

	tmpfn := filepath.Join(dir, model+"_tmp.go")
	if err := ioutil.WriteFile(tmpfn, content, 0666); err != nil {
		log.Fatal(err)
	}

	cmd := exec.Command("go", "run", tmpfn)
	var stdout bytes.Buffer
	cmd.Stdout = &stdout
	if err := cmd.Run(); err != nil {
		log.Fatal(err)
	}

	fmt.Println(stdout.String())
}

func main() {
	var wg sync.WaitGroup
	wg.Add(len(models))

	for _, model := range models {
		go func(model string) {
			createProgram(model)
			wg.Done()
		}(model)
	}

	wg.Wait()
	fmt.Println("done")
}
