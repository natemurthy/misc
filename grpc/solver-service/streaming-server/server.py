#!/bin/python3

import grpc
import math
import numpy as np
import solver_pb2
import solver_pb2_grpc
import time

from solver_pb2 import SolverResponse
from concurrent import futures


_ONE_DAY_IN_SECONDS = 60 * 60 * 24


def _solve_quadratic(a,b,c):
    radicand = math.pow(b,2) - 4*a*c
    if radicand > 0:
        radical = math.sqrt(radicand)
        plus  = -b + radical
        minus = -b - radical
        return plus/(2*a), minus/(2*a)


def _solve_newton(poly, x0, e, resp):
    f = np.poly1d(poly)
    df = f.deriv(m=1)
    delta = _dx(f, x0)
    while delta > e:
        msg = 'Converging: delta=%.9f' % delta
        x0 = x0 - f(x0)/df(x0)
        delta = _dx(f, x0)
        time.sleep(0.5)
        print(msg)
        yield resp(msg,None)
    print('Solution: %s' % str((x0,f(x0))))
    yield resp('complete', [x0, f(x0)])


def _dx(f,x):
    return abs(0-f(x))


class SolverService(solver_pb2_grpc.SolverServicer):

    def __init__(self):
        pass

    def SolveQuadratic(self, request, context):
        print('Received request: poly=%s' % request.polynomial)
        poly_coeffs = request.polynomial
        result = _solve_quadratic(*poly_coeffs)
        print('Solution: %s' % str(result))
        return self._make_response('complete',result)

    def SolveNewton(self, request, context):
        print('Received request: poly=%s, initial_guess=%f' % 
                (request.polynomial, request.initial_guess))
        return _solve_newton(
                request.polynomial, 
                request.initial_guess, 
                1e-32, 
                resp=self._make_response)
        
    def _make_response(self, msg, soln):
        if soln is None:
            return SolverResponse(solver_message=msg)
        else:
            return SolverResponse(
                    solver_message='complete',
                    solution=SolverResponse.Solution(x=soln[0],y=soln[1]))


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
