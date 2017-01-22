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
0.004831534
threads/java$ java par
1.76154E-4
```

C
```
threads/c$ ./seq
179148114 nanoseconds
threads/c$ ./par
89793314 nanoseconds
```

Go
```
threads/go$ go run seq.go
33.631265ms
threads/go$ go run par.go
21.702691ms
```
