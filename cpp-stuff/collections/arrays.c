#include <stdio.h>
#include <stdlib.h>

size_t len(int arr[]) {
  // array decays to pointer
  return ( sizeof arr / sizeof arr[0] );
}

int main() {
  int arr[5];
  for (int i = 0; i < 5; i++) {
    arr[i] = 10 + i;
    printf("%d\n", arr[i]);
  }  
  printf("Array length: %zu\n", sizeof arr / sizeof(int));
  printf("Array length: %zu\n", len(arr));
  exit(0);
}
