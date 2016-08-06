#include <iostream>

using namespace std;

int a = 1; int b = 1; int c = 1;
int *x = &a; int *y = &b; int *z = &c;

int main()
{
  cout << ++x << endl;
  cout << ++y << endl;
  cout << ++z << endl;
  return 0;
}

