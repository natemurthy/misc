import Dependencies._
import sbt._

name := "app-name"

lazy val commonSettings = Seq(
  // build settings
  scalaVersion in ThisBuild := "2.11.8",
  organization in ThisBuild := "natemurthy",

  // depenencies
  libraryDependencies ++= Seq(
    "org.scalatest"    %% "scalatest" % scalaTestVersion % "test"
  )
)

lazy val common = (project in file("common")).settings(commonSettings)

lazy val `service-1` = (project in file("services/service-1"))
                         .enablePlugins(PlayScala)
                         .dependsOn(common)
                         .settings(commonSettings)

lazy val `service-2` = (project in file("services/service-2"))
                         .enablePlugins(PlayScala)
                         .dependsOn(common)
                         .settings(commonSettings)
