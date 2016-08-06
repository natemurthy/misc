#include <iostream>

using namespace std;

int count;

void foo()
{
  int count;
  count = 1234;
  cout << count << endl;
  ::count = 5678;
}


int main()
{
  foo();
  cout << count << endl;
  return 0;
}
