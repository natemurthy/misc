#include <stdio.h>

// https://stackoverflow.com/questions/2660997/implementing-the-modulo-operator-as-a-function-in-c
// If the quotient a/b is representable, the expression (a/b)*b + a%b shall equal a
// (C99 standard, 6.5.5/6)
int main()
{
  int c=9, m=3, result=c-(c/m*m);
  printf("%d\n", result);
}
