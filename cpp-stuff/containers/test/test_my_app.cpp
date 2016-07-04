#include "gtest/gtest.h"
#include "containers.hpp"
#include "test_my_app.hpp"

ContainerTest::ContainerTest() {};

ContainerTest::~ContainerTest() {};

void ContainerTest::SetUp() {};

void ContainerTest::TearDown() {};

TEST(ContainerTest, IsAlive) {
  Container *c = new Container;
  EXPECT_TRUE(c->isAlive());
}

TEST(ContainerTest, SayHello) {
  Container *c = new Container;
  EXPECT_EQ(c->sayHello(), "Hello, I am a container");
}

