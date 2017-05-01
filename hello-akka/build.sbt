import sbt._

name := "hello-akka"

scalaVersion in ThisBuild := "2.11.8"

libraryDependencies ++= Seq(
  "com.typesafe.akka"  %% "akka-actor"   % "2.4.2",
  "com.typesafe.akka"  %% "akka-testkit" % "2.4.2",
  "org.scalatest"      %% "scalatest"    % "2.2.6" % "test"
)

