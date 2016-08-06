import sbt._

name := "sbt-buildinfo-example"

version := "1.0"

scalaVersion in ThisBuild := "2.11.8"

lazy val root = (project in file(".")).
  enablePlugins(BuildInfoPlugin).
  settings(
    buildInfoKeys := Seq[BuildInfoKey](name, version, scalaVersion, sbtVersion),
    buildInfoPackage := "info"
  )
