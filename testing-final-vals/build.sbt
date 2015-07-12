import sbt._

name := "testing-final-vals"

version := "1.0"

scalaVersion in ThisBuild := "2.11.6"

ScoverageSbtPlugin.ScoverageKeys.coverageMinimum := 50 
ScoverageSbtPlugin.ScoverageKeys.coverageFailOnMinimum := true

libraryDependencies +=  "org.scalatest" %% "scalatest" % "2.2.4" % "test"
