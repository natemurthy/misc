from grpc.tools import protoc

protoc.main(
    (
      '',
      '--proto_path=../idl',
      '--python_out=.',
      '--grpc_python_out=.',
      '../idl/solver.proto'
    )
)
