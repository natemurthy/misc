GATEWAY_FLAGS := -I. -I/usr/local/include -I$(GOPATH)/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis -I/usr/local/include

GRPC_FLAGS := --python_out=. --grpc_python_out=.


code:
	#python -m grpc_tools.protoc $(GRPC_FLAGS) $(GATEWAY_FLAGS) *.proto
	./codegen.sh

gw:
	protoc $(GATEWAY_FLAGS) \
		--go_out=Mgoogle/api/annotations.proto=github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api,plugins=grpc:. \
		--grpc-gateway_out=logtostderr=true:. \
		*.proto

deps:
	go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-grpc-gateway
	go get -u github.com/grpc-ecosystem/grpc-gateway/protoc-gen-swagger
	go get -u github.com/golang/protobuf/protoc-gen-go
