#include <iostream>

using namespace std;

class Animal
{
  public:
  void eat() { cout << "I'm eating generic food." << endl; }
};

class Cat : public Animal
{
  public:
  void eat() { cout << "I'm eating a rat." << endl; }
};

class Dog : public Animal
{
public:
  void eat();
};

void Dog::eat()
{
  cout << "I'm eating dog food." << endl;
}


class NonAnimal
{
  public:
    virtual void eat();
};

void NonAnimal::eat()
{
  cout << "I don't eat" << endl;
}


class Foo
{
public:
  std::string foo();
};

std::string Foo::foo()
{
  return "foo";
}

int main()
{
  Animal *animal = new Animal;
  Cat *cat = new Cat;
  Dog *dog = new Dog;
  NonAnimal *non = new NonAnimal;
  Foo *foo = new Foo;

  animal->eat(); // outputs: "I'm eating generic food."
  cat->eat();
  dog->eat();
  non->eat();
  cout << foo->foo() << endl;
}
