import sbt._

name := "orientdb-scala"

version := "1.0"

scalaVersion in ThisBuild := "2.11.6"

libraryDependencies +=  "com.orientechnologies" % "orientdb-graphdb" % "2.0.12"
