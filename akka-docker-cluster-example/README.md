akka-docker-cluster-example
===========================

An example akka-cluster project with docker support. See [the blog post](http://blog.michaelhamrah.com/2014/11/clustering-akka-applications-with-docker-version-3/). Uses [SBT Native Packager](https://github.com/sbt/sbt-native-packager).

### How to Run

In SBT, just run `docker:publishLocal` to create a local docker container. 

To run the cluster, run `docker-compose up`. This will create 3 nodes, a seed and two regular members, called `seed`, `c1`, and `c2` respectively.

Or run each container separately with:

```
docker run --rm -it --name seed mhamrah/clustering:0.3
docker run --rm -it --name member1 --link seed:seed mhamrah/clustering:0.3
docker run --rm -it --name member2 --link seed:seed mhamrah/clustering:0.3
```

While running, try opening a new terminal and (from the same directory) try things like `docker-compose down seed` and watch the cluster nodes respond.

Enable JMX monitoring with:

```
./target/universal/stage/bin/clustering \
  -Dcom.sun.management.jmxremote.port=9999
  -Dcom.sun.management.jmxremote.authenticate=false \
  -Dcom.sun.management.jmxremote.ssl=false
```
