import sbt._

name := "window-wordcount"

libraryDependencies ++= Seq(
  "org.apache.flink" % "flink-streaming-scala" % "0.10.1"
)

