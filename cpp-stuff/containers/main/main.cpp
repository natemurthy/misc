#include <iostream>
#include <unistd.h>
#include "containers.hpp"

using namespace std;

void printStatus(Container *c)
{
  switch (c->getStatus()) {
    case Created:
      cout << "Container " + c->getId() + " is created" << endl;
      break;
    case Running:
      cout << "Container " + c->getId() + " is running" << endl;
      break;
    case Stopped:
      cout << "Container " + c->getId() + " is stopped" << endl;
      break;
  }
}

int main()
{
  Container *c = new Container;
  printStatus(c);
  usleep(2000000);

  c->start();
  printStatus(c);
  usleep(4000000);

  c->stop();
  printStatus(c);
  return 0;
}
