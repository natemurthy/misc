import sbt._

name := """json4s-vs-playjson"""

version := "0.1-SNAPSHOT"

lazy val root = (project in file(".")).enablePlugins(PlayScala)

scalaVersion in ThisBuild := "2.11.6"

scalacOptions ++= Seq(
  "-feature",
  "-language:postfixOps"
)

resolvers ++= Seq(
  "Sonatype Releases" at "https://oss.sonatype.org/content/repositories/releases/"
)

libraryDependencies ++= Seq(
  "com.github.tototoshi" %% "play-json4s-jackson" % "0.4.0", 
  "org.json4s"           %% "json4s-jackson"      % "3.2.11"
)
