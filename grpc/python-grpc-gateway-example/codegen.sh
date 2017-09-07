
# Generate Python code for server and client stubs

export PY_SITE_PACKAGES="./venv/lib/python3.5/site-packages/"

python -m grpc_tools.protoc \
  -I $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=$PY_SITE_PACKAGES \
  --grpc_python_out=$PY_SITE_PACKAGES \
  $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api/annotations.proto

python -m grpc_tools.protoc \
  -I $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=$PY_SITE_PACKAGES \
  --grpc_python_out=$PY_SITE_PACKAGES \
  $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis/google/api/http.proto

python -m grpc_tools.protoc \
  -I . -I $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --python_out=. --grpc_python_out=. \
  helloworld.proto

touch $PY_SITE_PACKAGES/google/__init__.py
touch $PY_SITE_PACKAGES/google/api/__init__.py


# Generate Go code for gateway proxy server

protoc  -I $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --proto_path=. \
  --grpc-gateway_out=logtostderr=true:. \
  helloworld.proto

protoc  -I $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --proto_path=. \
  --grpc-gateway_out=logtostderr=true:. \
  --go_out=plugins=grpc:. \
  helloworld.proto

mkdir helloworld
mv helloworld.pb.* helloworld/

# Generate Swagger docs

protoc -I $GOPATH/src/github.com/grpc-ecosystem/grpc-gateway/third_party/googleapis \
  --proto_path=. \
  --swagger_out=logtostderr=true:. \
  helloworld.proto

