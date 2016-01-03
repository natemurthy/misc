import sbt._

name := "wordcount"

libraryDependencies ++= Seq(
  "org.apache.flink" % "flink-scala" % "0.10.1"
)

