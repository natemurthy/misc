# grpcurl-ping

If you use IP address
```
$ grpcurl -v -plaintext 127.0.0.1:50051 list
Failed to list services: rpc error: code = Unavailable desc = all SubConns are in TransientFailure, latest connection error: <nil>
```
instead of hostname
```
$ grpcurl -v -plaintext localhost:50051 list
Ping`
grpc.reflection.v1alpha.ServerReflection
```
reflection won't quite work.
