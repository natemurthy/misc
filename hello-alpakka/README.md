# hello-alpakka

A very simple consumer that gets anyone started with Typesafe/Lightbend's
[akka-stream-kafka](https://github.com/akka/alpakka-kafka) library

Build with

```
sbt clean assembly
```

and run the binary using:

```
scala target/scala-2.12/hello-alpakka-assembly-0.1.jar $BROKER_URLS
```

where the BROKER_URLS env variable is a comman-sparated listed of broker locations.
