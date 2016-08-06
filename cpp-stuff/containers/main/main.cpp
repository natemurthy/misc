#include <iostream>
#include <unistd.h>
#include "containers.hpp"

using namespace std;

void printStatus(Container *c)
{
  switch (c->getStatus()) {
    case Created:
      cout << "Container " + c->getId() + " created" << endl;
      break;
    case Running:
      cout << "Container " + c->getId() + " is running" << endl;
      break;
    case Stopped:
      cout << "Container " + c->getId() + " has stopped" << endl;
      break;
  }
}

int main()
{
  Container *c = new Container;
  printStatus(c);
  usleep(1.5*1e6); // thread sleep microsceconds

  c->start();
  printStatus(c);
  usleep(4*1e6);

  c->stop();
  printStatus(c);
  return 0;
}
