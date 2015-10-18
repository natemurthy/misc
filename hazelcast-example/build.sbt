name := "hazelcast-example"

scalaVersion in ThisBuild := "2.11.7"

val version = "3.5.3"

libraryDependencies ++= Seq(
  "com.hazelcast" % "hazelcast"       % version,
  "com.hazelcast" % "hazelcast-cloud" % version
)

