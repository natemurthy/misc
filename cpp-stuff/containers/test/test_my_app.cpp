#include "gtest/gtest.h"
#include "containers.hpp"
#include "test_my_app.hpp"

ContainerTest::ContainerTest() {};

ContainerTest::~ContainerTest() {};

void ContainerTest::SetUp() {};

void ContainerTest::TearDown() {};

TEST(ContainerTest, GetId) {
  Container *c = new Container;
  EXPECT_EQ(c->getId().length(), 12);
}

TEST(ContainerTest, IsCreated) {
  Container *c = new Container;
  EXPECT_EQ(c->getStatus(), Created);
}

TEST(ContainerTest, IsRunning) {
  Container *c = new Container;
  c->start();
  EXPECT_EQ(c->getStatus(), Running);
}

TEST(ContainerTest, HasStopped) {
  Container *c = new Container;
  c->stop();
  EXPECT_EQ(c->getStatus(), Stopped);
}

