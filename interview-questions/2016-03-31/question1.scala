// Question 1

object Test extends App {
  case class Person(var age: Int)

  def person: Person = Person(10)

  person.age = person.age + 1 // what's happening here

  val newPerson = person
  newPerson.age = newPerson.age + 1 // vs happening here

  println(person) // Person(10)
  println(newPerson) // Person(11)
}
