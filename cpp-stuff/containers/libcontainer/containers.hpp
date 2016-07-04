#include <stdlib.h>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

class Container
{
public:
  Container();
  ~Container();
  bool isAlive();
  void kill();
  virtual std::string sayHello();
private:
  bool __alive;
};
