#include <stdlib.h>
#include <chrono>
#include <iostream>
#include <random>
#include <string>
#include <cstdlib>

#include "containers.hpp"

static std::string random_string(int length)
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

Container::Container()
{
  Container::status = Created;
  Container::id = random_string(12);
}

std::string Container::getId()
{
  return Container::id;
}

Status Container::getStatus()
{
  return Container::status;
}

void Container::start()
{
  Container::status = Running;
}

void Container::stop()
{
  Container::status = Stopped;
}
