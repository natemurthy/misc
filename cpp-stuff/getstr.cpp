#include <iostream>

using namespace std;

// function prototype
//void getstr(char *s);

void getstr(char *s)
{
  cin >> s;
}

// global string buffer
char input[128];

int main()
{
  cout << "Enter a string: ";
	getstr(input);
	cout << "You enetered: " << input << endl;
	return 0;
}
