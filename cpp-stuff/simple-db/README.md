# simple-db

Writing a sqlite clone from scratch in C using only the standard library
[https://cstack.github.io/db_tutorial](https://cstack.github.io/db_tutorial)

## Build
```
gcc db.c -o db
```

## Run
```
./db test.db

db > insert 1 cstack foo@bar.com
Executed.
db > insert 2 bob bob@example.com
Executed.
db > select
(1, cstack, foo@bar.com)
(2, bob, bob@example.com)
Executed.
db > insert foo bar 1
Syntax error. Could not parse statement.
db > .exit
```
