package main

import (
	"flag"
	"log"

	pb "github.com/natemurthy/solver-client/idl"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
)

const (
	address = "localhost:50051"
)

func parseInputs() (float64, float64, float64) {
	a := flag.Float64("a", 0.0, "second-degree coefficient")
	b := flag.Float64("b", 0.0, "first-degree coefficient")
	c := flag.Float64("c", 0.0, "zero-degree coefficient")
	flag.Parse()
	return *a, *b, *c
}

func main() {
	a, b, c := parseInputs()
	// Set up a connection to the server.
	conn, err := grpc.Dial(address, grpc.WithInsecure())
	if err != nil {
		log.Fatalf("did not connect: %v", err)
	}
	defer conn.Close()
	client := pb.NewSolverClient(conn)

	soln, err := client.SolveQuadratic(
		context.Background(), &pb.SolverRequest{a, b, c})
	if err != nil {
		log.Fatalf("could not solve: %v", err)
		return
	}
	log.Printf("Solution is %s", soln)
}
