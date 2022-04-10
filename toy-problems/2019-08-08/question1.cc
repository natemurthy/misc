/*

Given an array of integers, determine whether the array only increases or only decreases.

Examples:

 [1, 2, 3] --> True
 [3, 2, 1] --> True
 [1, 2, 4, 4, 5] --> True
 [1, 1, 1] --> True

Solution provided below in the expected C/C++ function signature of the original prompt.

Compile and run using:
```
$ clang++ -std=c++11 -stdlib=libc++ question1.cc; ./a.out
```
*/
#include <iostream>
#include <vector>

using namespace std;

bool verify(const vector<int>& vec) {
  bool is_monotonic = true;
  int cursor = 0;
  int end = vec.size()-1;

  if (end < 2) return is_monotonic;

  for (int i = cursor; i < end; i++) {
    if (vec.at(i) == vec.at(i+1)) cursor++;
    else break;
  }

  if (cursor == end) return is_monotonic;

  bool is_decreasing = vec.at(cursor) > vec.at(cursor+1);

  cursor++;

  if (is_decreasing) {
    for (int i = cursor; i < end; i++) {
      if (vec.at(i) < vec.at(i+1)) {
        is_monotonic = false;
        break;
      }
    }
  } else {
    for (int i = cursor; i < end; i++) {
      if (vec.at(i) > vec.at(i+1)) {
        is_monotonic = false;
        break;
      }
    }
  }

  return is_monotonic;
}

void print(bool b) {
  if (b) {
    cout << "True" << endl;
    return;
  }
  cout << "False" << endl;
}

int main() {
  print(verify({1,2,1}));
  print(verify({1,2,4,4,5}));
  print(verify({1,1,1}));
  print(verify({0,3,1,1,0,0,-1,-2}));
}

