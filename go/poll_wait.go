package main

import (
	"fmt"
	"net"
	"os"
	"runtime"
	"time"
)

// https://github.com/golang/go/issues/30957
//
// Sample code to reliably reproduce runtime deadlock bug in runtime_pollWait.
// The code below was tested on my laptop with golang 1.12.4 and netcat.
// Bug appears fixed in go 1.12.5

var tty *os.File

func main() {

	var err error

	// Open TTY

	tty, err = os.Open("/dev/tty")
	if err != nil {
		fmt.Println("Error opening TTY:", err.Error())
		os.Exit(1)
	}
	defer tty.Close()

	// Listen for incoming connections

	l, err := net.Listen("tcp", "0.0.0.0:2019")
	if err != nil {
		fmt.Println("Error listening:", err.Error())
		os.Exit(1)
	}

	fmt.Println("GOMAXPROCS =", runtime.GOMAXPROCS(0))

	// Close the listener when the application closes

	defer l.Close()
	fmt.Println("Listening on port 2019")

	// Listen for an incoming connection

	for {
		conn, err := l.Accept()
		if err != nil {
			fmt.Println("Error accepting:", err.Error())
			os.Exit(1)
		}
		go connection_handler(conn)
	}
}

func connection_handler(conn net.Conn) {

	fmt.Println("Connection accepted:", conn.RemoteAddr())

	// Close connection on completion

	defer conn.Close()

	// Use ticker to send data at fixed intervals

	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()

	// Connection loop

	for {
		// Read data

		msg, err := read_tty(tty)
		if err != nil {
			if os.IsTimeout(err) {
				continue
			}
			fmt.Println("Error preparing message:", err.Error())
			break
		}

		// Send data

		_, err = conn.Write([]byte(msg))
		if err != nil {
			break
		}

		fmt.Print(".")

		// Wait for ticket trigger

		<-ticker.C
	}

	// Done

	fmt.Println("Connection closed:", conn.RemoteAddr())
}

func read_tty(f *os.File) ([]byte, error) {

	// Set tiny read timeout

	err := f.SetDeadline(time.Now().Add(time.Millisecond))
	if err != nil {
		return nil, err
	}

	// Read few bytes

	data := make([]byte, 10)

	_, err = f.Read(data)
	if err != nil {
		return nil, err
	}

	// Done

	return data, nil
}
