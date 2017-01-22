#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>

#define BILLION 1000000000L

void *countdown( void *args) {
  int n = ((intptr_t) args) / 2;
  while (n > 0) {
    n -= 1;
  }
}

main() {
  int COUNT = 80000000;
  pthread_t thread1, thread2;
  int  iret1, iret2;

  uint64_t diff;
  struct timespec start, end;

  clock_gettime(CLOCK_MONOTONIC, &start);
  iret1 = pthread_create( &thread1, NULL, &countdown, (void*) (intptr_t) COUNT);
  iret2 = pthread_create( &thread2, NULL, &countdown, (void*) (intptr_t) COUNT);
  pthread_join( thread1, NULL);
  pthread_join( thread2, NULL); 
  clock_gettime(CLOCK_MONOTONIC, &end);

  diff = BILLION * (end.tv_sec - start.tv_sec) + end.tv_nsec - start.tv_nsec;
  printf("elapsed time = %llu nanoseconds\n", (long long unsigned int) diff);

  exit(0);
}


