#include <stdlib.h>
#include <list>
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

enum Status { Created, Running, Pausing, Paused, Stopped };

class Container
{
public:
  Container();
  ~Container();
  virtual std::string getId();
  virtual Status getStatus();
  void start();
  void stop();
private:
  Status status;
  std::string id;
};
