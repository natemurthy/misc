#include <iostream>

using namespace std;

double d = 3.141459;
double &ref()
{
  return d;
}

int main()
{
  cout << ref() << endl;
  ref() = 2.789;
  cout << ref() << endl;
  return 0;
}
