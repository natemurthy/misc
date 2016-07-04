#include <iostream>
#include "containers.hpp"

using namespace std;

void callVirtual(Container *c)
{
  if (c->isAlive())
    cout << c->sayHello() << endl;
  else
    cout << "Container is dead" << endl;
}

int main()
{
  Container *c = new Container;
  callVirtual(c);

  cout << "Going to kill this container" << endl;
  c->kill();
  callVirtual(c);

  return 0;
}
