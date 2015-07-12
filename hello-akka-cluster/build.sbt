import sbt._

name := "hello-akka-cluster"

scalaVersion in ThisBuild := "2.11.6"

libraryDependencies ++= Seq(
  "com.typesafe.akka" %% "akka-actor"      % "2.3.10",
  "com.typesafe.akka" %% "akka-cluster"    % "2.3.10",
  "com.typesafe.akka" %% "akka-slf4j"      % "2.3.10",
  "ch.qos.logback"    %  "logback-classic" % "1.1.2"
)
