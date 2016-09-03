#include <iostream>
#include <time.h>

using namespace std;


int main()
{
  timespec time;
  //clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &time);
  clock_gettime(CLOCK_MONOTONIC, &time);
  cout << time.tv_sec << ":" << time.tv_nsec << endl;
  return 0;  
}
