#include <iostream>

using namespace std;

// function prototype
//void getstr(char *s);

void getstr(char *s)
{
  cin >> s;
}

string foo()
{
  return "foo";
}

// global string buffer
char input[128];

int main()
{
  //cout << "Enter a string: ";
  //getstr(input);
  //cout << "You enetered: " << input << endl;
  cout << foo() << endl;
  return 0;
}
