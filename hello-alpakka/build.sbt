name := "hello-alpakka"

version := "0.1"
scalaVersion := "2.12.6"
sbtVersion := "1.2.1"

libraryDependencies ++= Seq(
  "com.typesafe.akka" %% "akka-stream-kafka" % "0.22"
)

