# hello-alpakka

A very simple consumer that gets anyone started with Typesafe/Lightbend's
[akka-stream-kafka](https://github.com/akka/alpakka-kafka) library

Build with

```
sbt clean assembly
```

and run the binary using:

```
BROKER_URLS="broker1:9092,broker2:9092" TOPIC="streams-plaintext-input" GROUP_ID="test-group1" \
scala target/scala-2.12/hello-alpakka-assembly-0.1.jar
```

where the BROKER_URLS env variable is a comma-separated list of broker locations.
