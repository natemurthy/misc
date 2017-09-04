#!/bin/python3

import grpc
import math
import solver_pb2
import solver_pb2_grpc
import time

from concurrent import futures


_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def _solve_quadratic(a,b,c):
    radicand = math.pow(b,2) - 4*a*c
    if radicand > 0:
        radical = math.sqrt(radicand)
        plus  = -b + radical
        minus = -b - radical
        return plus/(2*a), minus/(2*a)


class SolverService(solver_pb2_grpc.SolverServicer):

    def __init__(self):
        pass

    def SolveQuadratic(self, request, context):
        print('Received request:\n%s' % request)
        a = request.a
        b = request.b
        c = request.c
        result = _solve_quadratic(a,b,c)
        if result is None:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('No real-valued solution')
            return solver_pb2.SolverResponse(x=None,y=None)
        return solver_pb2.SolverResponse(x=result[0],y=result[1])


def serve(port_binding):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    solver_pb2_grpc.add_SolverServicer_to_server(SolverService(), server)
    print('SolverService running on %s' % port_binding)
    server.add_insecure_port(port_binding)
    server.start()
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve('[::]:50051')
