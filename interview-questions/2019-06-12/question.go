package main

import (
	"flag"
	"fmt"
	"io/ioutil"
	"os"
)

var fs FileSystem

// FileSystem API to be implemented
type FileSystem interface {
	// List all the files and directories specified at the path (given)
	List(path string) []string

	// Delete will delete empty directory or file specified
	// by absolute path (given)
	Delete(path string) bool

	// IsDirectory returns true if the path supplied is a folder
	// and not a file (given)
	IsDirectory(path string) bool

	// DeleteAll will remove an entire file system directory tree
	// regardless of whether it is empty or not.
	//
	// TODO: interview question is to implement this function
	DeleteAll(dir string) bool
}

type fileSystem struct{}

// List is given
func (fs *fileSystem) List(path string) []string {
	contents, err := ioutil.ReadDir(path)
	if err != nil {
		panic(err)
	}

	var names []string
	for _, f := range contents {
		names = append(names, f.Name())
	}
	return names
}

// IsDirectory is given
func (fs *fileSystem) IsDirectory(path string) bool {
	info, err := os.Lstat(path)
	if err != nil {
		panic(err)
	}
	return info.Mode().IsDir()
}

// Delete is given
func (fs *fileSystem) Delete(path string) bool {
	return os.Remove(path) == nil
}

// DeleteAll is a composition of all the given functions above and
// whose behavior should be compared to os.RemoveAll with respect
// to correctness and performance.
//
// TODO implement this method
func (fs *fileSystem) DeleteAll(path string) bool {
	var contents []string

	if fs.IsDirectory(path) {
		contents = fs.List(path)
	}

	allDeleted := true
	for _, d := range contents {
		fullpath := fmt.Sprintf("%s/%s", path, d)
		allDeleted = allDeleted && fs.DeleteAll(fullpath)
	}

	return allDeleted && fs.Delete(path)
}

func main() {
	fs = new(fileSystem)

	fmt.Println("fs.List before:", fs.List("."))

	// Steps to reproduce benchmark test results:
	//
	// 1. Copy contents of $GOPATH to the parent folder of this question.go file
	//    ```
	//    nate:2019-06-12$ time cp -r $GOPATH . &> /dev/null; mv Gospace test-dir
	//    0.54s user 13.52s system 89% cpu 15.715 total
	//    ```
	//
	// 2. os.RemoveAll runtime (does this ):
	//    ```
	//    nate:2019-06-12$ time go run question.go -r
	//    fs.List before: [emptydir file.txt question.go test-dir]
	//    fs.List after : [emptydir file.txt question.go]
	//    go run question.go -r  0.93s user 7.25s system 111% cpu 7.345 total
	//    ```
	//
	// 3. fs.DeleteAll runtime:
	//    ```
	//    nate:2019-06-12$ time go run question.go -d
	//    fs.List before: [emptydir file.txt question.go test-dir]
	//    fs.List after : [emptydir file.txt question.go]
	//    go run question.go  1.36s user 9.10s system 116% cpu 9.021 total
	//    ```

	if *rflag {
		os.RemoveAll("test-dir")
	} else if *dflag {
		fs.DeleteAll("test-dir")
	} else {
		flag.Usage()
	}

	fmt.Println("fs.List after :", fs.List("."))
}

var (
	rflag = flag.Bool("r", false, "remove all")
	dflag = flag.Bool("d", false, "delete all")
)

func init() {
	flag.Parse()
}
