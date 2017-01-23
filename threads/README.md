## Thread experiments

In each example we countdown from 80 million by 1 in a single-threaded and multithreaded manner, respectively, and measure the elapsed time for each case. These tests were compiled and executed on an Asus Zenbook UX31A, Intel Core i7 3517U 1.9 GHz dual core with hyperthreading, 4 GB RAM, running Ubuntu 12.04 Desktop.

Python
```
threads/python$ python seq.py
3.46064090729
threads/python$ python par.py
5.86907505989
```

C#
```
threads/csharp$ mono Seq.exe
00:00:00.0290179
threads/csharp$ mono Par.exe
00:00:00.0014183
```

Java
```
threads/java$ java seq
elapsed time = 4698598 nanoseconds
threads/java$ java par
elapsed time = 146954 nanoseconds
```

C
```
threads/c$ ./seq
elapsed time = 179148114 nanoseconds
threads/c$ ./par
elapsed time = 89793314 nanoseconds
```

Go
```
threads/go$ go run seq.go
34.92398ms
threads/go$ go run par.go
15.952245ms
```
