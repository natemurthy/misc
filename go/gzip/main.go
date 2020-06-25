package main

import (
	"bufio"
	"compress/gzip"
	"fmt"
	"io/ioutil"
	"math/rand"
	"os"
	"time"
)

var zipFile = "zipfile.gz"

func main() {
	writeZipAlt()
	readZip()
}

func writeZip() {
	handle, err := openFile(zipFile)
	if err != nil {
		fmt.Println("[ERROR] Opening file:", err)
	}

	zipWriter, err := gzip.NewWriterLevel(handle, 9)
	if err != nil {
		fmt.Println("[ERROR] New gzip writer:", err)
	}
	data := randString(10 * 1024 * 1024)
	//data := "Hello, World!\n"
	numberOfBytesWritten, err := zipWriter.Write([]byte(data))
	if err != nil {
		fmt.Println("[ERROR] Writing:", err)
	}
	err = zipWriter.Close()
	if err != nil {
		fmt.Println("[ERROR] Closing zip writer:", err)
	}
	fmt.Println("[INFO] Number of bytes written:", numberOfBytesWritten)

	closeFile(handle)
}

func writeZipAlt() {
	f, err := ioutil.TempFile(".", "tmp-")
	if err != nil {
		panic(err)
	}

	bufw := bufio.NewWriter(f)
	zipWriter, err := gzip.NewWriterLevel(bufw, gzip.BestCompression)
	if err != nil {
		panic(err)
	}

	//data := randString(10 * 1024)
	data := "hello world!\n  here are some special chars @#$%^^&*()-_=+[];',./\\{}|:\"<>?"
	n, err := zipWriter.Write([]byte(data))
	if err != nil {
		panic(err)
	}

	fmt.Println("[INFO] Number of bytes written to tmp file:", n)

	if err := zipWriter.Close(); err != nil {
		panic(err)
	}

	if err := bufw.Flush(); err != nil {
		panic(err)
	}

	f.Sync()

	closeFile(f)

	os.Rename(f.Name(), zipFile)
}

func readZip() {
	handle, err := openFile(zipFile)
	if err != nil {
		fmt.Println("[ERROR] Opening file:", err)
	}

	zipReader, err := gzip.NewReader(handle)
	if err != nil {
		fmt.Println("[ERROR] New gzip reader:", err)
	}
	defer zipReader.Close()

	fileContents, err := ioutil.ReadAll(zipReader)
	if err != nil {
		fmt.Println("[ERROR] ReadAll:", err)
	}

	numberOfBytesRead := len([]byte(fileContents))
	fmt.Printf("[INFO] Number of bytes read: %d\n", numberOfBytesRead)

	// ** Another way of reading the file **
	//
	// fileInfo, _ := handle.Stat()
	// fileContents := make([]byte, fileInfo.Size())
	// bytesRead, err := zipReader.Read(fileContents)
	// if err != nil {
	//     fmt.Println("[ERROR] Reading gzip file:", err)
	// }
	// fmt.Println("[INFO] Number of bytes read from the file:", bytesRead)

	closeFile(handle)
}

func openFile(fileToOpen string) (*os.File, error) {
	return os.OpenFile(fileToOpen, openFileOptions, openFilePermissions)
}

func closeFile(handle *os.File) {
	if handle == nil {
		return
	}

	err := handle.Close()
	if err != nil {
		fmt.Println("[ERROR] Closing file:", err)
	}
}

const openFileOptions int = os.O_CREATE | os.O_RDWR
const openFilePermissions os.FileMode = 0660

const (
	letterBytes   = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
	letterIdxBits = 6                    // 6 bits to represent a letter index
	letterIdxMask = 1<<letterIdxBits - 1 // All 1-bits, as many as letterIdxBits
	letterIdxMax  = 63 / letterIdxBits   // # of letter indices fitting in 63 bits
)

func randString(n int) string {
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
	return string(b)
}
