package main

import (
	"context"
	"log"
	"net"

	"github.com/golang/protobuf/ptypes/empty"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"

	pb "github.com/natemurthy/misc/go/grpcurl-ping/api"
)

type server struct{}

// Ping will return a Pong
func (s *server) Ping(ctx context.Context, req *empty.Empty) (*pb.Pong, error) {
	return &pb.Pong{Healthy: true}, nil
}

func newServer() (net.Listener, *grpc.Server) {
	s := grpc.NewServer()
	pb.RegisterPingServer(s, new(server))
	reflection.Register(s)
	host := ":50051"
	lis, err := net.Listen("tcp", host)
	if err != nil {
		log.Fatalf("failed to listen: %v", err)
	}
	log.Println("server listening on:", host)
	return lis, s
}

func main() {
	lis, s := newServer()
	s.Serve(lis)
}
