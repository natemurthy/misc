#include <stdlib.h>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

#include "containers.hpp"

Container::Container()
{
  Container::__alive = true;
}

bool Container::isAlive()
{
  return Container::__alive;
}

void Container::kill()
{
  Container::__alive = false;
}

std::string Container::sayHello()
{
  return "Hello, I am a container";
}
