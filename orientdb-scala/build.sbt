import sbt._

name := "orientdb-scala"

version := "1.0"

scalaVersion in ThisBuild := "2.11.7"

//scalacOptions in ThisBuild ++= Seq("-unchecked", "-deprecation")

libraryDependencies ++=  
Seq(
  "com.orientechnologies" %  "orientdb-graphdb" % "2.1.16",
  "org.scalatest"         %% "scalatest"        % "2.2.6" % "test"
)
