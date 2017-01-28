/*
 *  simple_process.cpp
 *
 *  Created on: Jun 26, 2015
 *  Author: Marco Massenzio
 */

#include <iostream>

#include <process/dispatch.hpp>
#include <process/future.hpp>
#include <process/process.hpp>

#include <stout/numify.hpp>


using std::cout;
using std::endl;

using process::Future;
using process::Promise;


class SimpleProcess : public process::Process<SimpleProcess> {
public:

  Future<Nothing> doSomething(const std::string msg) {
    std::cout << "Wrapping message: " << msg << std::endl;
    return Nothing();
  }

  Future<int> calc(int lhs, int rhs) {
    return Promise<int>(lhs + rhs).future();
  }

private:
  Promise<bool> shouldQuit;
};


int runProcess() {
  SimpleProcess simpleProcess;
  process::PID<SimpleProcess> pid = process::spawn(simpleProcess);

  cout << "Running simple process" << endl;

  cout << "Dispatching..." << endl;
  process::dispatch(
      pid, &SimpleProcess::doSomething, "test test test");

  Future<int> sum = process::dispatch(pid, &SimpleProcess::calc, 99, 101);
  sum.then([](int n) {
        cout << "99 + 101 = " << n << endl;
        return Nothing();
  });

  sum.await();
  process::terminate(simpleProcess);
  process::wait(simpleProcess);
  cout << "Done" << endl;

  return EXIT_SUCCESS;
}
