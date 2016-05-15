name := "hazelcast-example"

scalaVersion in ThisBuild := "2.11.8"

val hzVersion = "3.5.3"

libraryDependencies ++= Seq(
  "com.hazelcast" % "hazelcast"       % hzVersion,
  "com.hazelcast" % "hazelcast-cloud" % hzVersion
)

