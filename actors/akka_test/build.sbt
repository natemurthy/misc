import sbt._

name := """akka-test"""

version := "0.1-SNAPSHOT"

scalaVersion in ThisBuild := "2.11.1"

resolvers ++= Seq(
  "Sonatype Releases" at "https://oss.sonatype.org/content/repositories/releases/"
)

libraryDependencies ++= Seq(
  "com.typesafe.akka"   %% "akka-actor" % "2.3.4"
)

