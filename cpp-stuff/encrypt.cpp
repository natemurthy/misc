#include <iostream>
#include <cstring>

using namespace std;

char input[128];
char mask;
unsigned int i;

int main() {
  cout << "Enter a string to encrypt: ";
  cin.getline(input, sizeof(input));
  cout << "Enter a single-character mask: ";
  cin >> mask;
  cout << "Original string: " << input << endl;
  for (i = 0; i < strlen(input); i++)
    input[i] ^= mask;
  cout << "Encrypted string: " << input << endl;
  for (i = 0; i < strlen(input); i++)
    input[i] ^= mask;
  cout << "Decrypted string: " << input << endl;
  return 0;
}
