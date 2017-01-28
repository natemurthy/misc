/*
 * simple_server.cpp
 *
 * Created on: Jun 26, 2015
 * Author: Marco Massenzio, http://codetrips.com
 *
 * This code is explained in a blog entry at the above URL.
 */

#include <chrono>
#include <iostream>
#include <thread>

#include <process/delay.hpp>
#include <process/dispatch.hpp>
#include <process/future.hpp>
#include <process/process.hpp>


#include <stout/json.hpp>
#include <stout/numify.hpp>


using std::cerr;
using std::cout;
using std::endl;

using std::chrono::seconds;

using process::Future;
using process::Promise;

using process::http::Request;
using process::http::OK;
using process::http::InternalServerError;


class SimpleProcess : public process::Process<SimpleProcess> {

public:
  SimpleProcess() : ProcessBase("simple") {}

  virtual void initialize();

  Future<bool> done() {
    cout << "are we done yet? " << endl;
    return shouldQuit.future();
  }

  void shutdown() {
    cout << "Shutting down server..." << endl;
    this->shouldQuit.set(true);
  }

private:
  Promise<bool> shouldQuit;
};


void SimpleProcess::initialize() {
  route(
      "/add",
      "Adds the two query arguments",
      [] (Request request) {
        int a = numify<int>(request.query["a"]).get();
        int b = numify<int>(request.query["b"]).get();
        std::ostringstream result;
        result << "{ \"result\": " << a + b << "}";
        JSON::Value body = JSON::parse(result.str()).get();
        return OK(body);
  });
  route(
      "/quit",
      "Shuts the server down",
      [this] (Request request) {
        this->shutdown();
        return OK("Shutting down server");
  });
  route(
      "/error",
      "Forces an Internal Server Error (500)",
      [this](Request request) {
        this->shouldQuit.set(false);
        return InternalServerError("We encountered an error");
  });
}


int runServer() {
  int retCode;
  SimpleProcess simpleProcess;
  process::PID<SimpleProcess> pid = process::spawn(simpleProcess);

  cout << "Running Server on http://" << process::address().ip << ":"
       << process::address().port << "/simple" << endl
       << "Use /quit to terminate server..." << endl;

  cout << "Waiting for it to terminate..." << endl;
  Future<bool> quit = simpleProcess.done();
  quit.await();

  // wait for the server to complete the request
  std::this_thread::sleep_for(seconds(2));

  if (!quit.get()) {
    cerr << "The server encountered an error and is exiting now" << endl;
    retCode = EXIT_FAILURE;
  } else {
    cout << "Done" << endl;
    retCode = EXIT_SUCCESS;
  }

  process::terminate(simpleProcess);
  process::wait(simpleProcess);
  return retCode;
}
