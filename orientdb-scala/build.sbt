import sbt.

name := "orientdb-scala"

version := "1.0"

scalaVersion in ThisBuild := "2.11.6"

//scalacOptions in ThisBuild ++= Seq("-unchecked", "-deprecation")

libraryDependencies ++=  
Seq(
  "com.orientechnologies" %  "orientdb-graphdb" % "2.1.0",
  "org.scalatest"         %% "scalatest"        % "2.2.5" % "test"
)
