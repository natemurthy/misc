#include <chrono>
#include <iostream>
#include <random>
#include <string>
#include <cstdlib>

std::string random_string(int& length)
{
    static const std::string alphanums = "0123456789abcdef";

    thread_local static std::mt19937 rg{std::random_device{}()};
    thread_local static std::uniform_int_distribution<> pick(0, alphanums.size() - 1);

    std::string s;

    s.reserve(length);

    while(length--)
        s += alphanums[pick(rg)];

    return s;
}

int main(int argc, char **argv)
{
  int len = atoi(argv[1]);
  std::cout << random_string(len) << std::endl;
  return 0;
}
