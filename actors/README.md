## Actors

Quick performance omparison of Akka (a JVM-based actor implementation) and Pykka (a Python-based
actor implementation inspired by Akka). In the examples below, we send 1 million messages to an actor 
that assigns the message count to an internal variable. These tests were compiled and executed on an 
Asus Zenbook UX31A, Intel Core i7 3517U 1.9 GHz dual core with hyperthreading, 4 GB RAM, running 
Ubuntu 12.04 Desktop.

Pykka:
```
actors/pykka_test$ python pykka_test.py 
Time to process 1000000 messages: 39.611623 s
```

Akka:
```
actors/akka_test$ sbt run
[info] Set current project to akka-test
[info] Running AkkaTest 
Time to process 1000000 messages: 0.335407321 s
```


