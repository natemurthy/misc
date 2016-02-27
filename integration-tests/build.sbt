import sbt._

name := "integration-tests"

version := "1.0"

scalaVersion in ThisBuild := "2.11.7"


libraryDependencies ++=  
Seq(
  "com.thenewmotion.akka" %% "akka-rabbitmq"    % "2.2",
  "com.orientechnologies" %  "orientdb-graphdb" % "2.1.11",
  "org.scalatest"         %% "scalatest"        % "2.2.6" % "test"
)

resolvers += "The New Motion Public Repo" at "http://nexus.thenewmotion.com/content/groups/public/"

