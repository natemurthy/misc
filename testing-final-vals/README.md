# testing-final-vals

Execute tests using
```
$ sbt clean coverage test
```

Intuitively one would expect to get 100% coverage the way the code is written, however in actuality only 50% coverage is achieved due to the nature of how `final val` is converted to bytecode. 

See: http://stackoverflow.com/questions/31285452/why-when-i-unit-test-do-i-get-coverage-points-with-final-lazy-val-but-not-fin
