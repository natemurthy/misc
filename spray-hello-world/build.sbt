import sbt._
import Keys._
import spray.revolver.RevolverPlugin.Revolver

name := "spray-hello-world"
version := "1.0"
scalaVersion := "2.11.6"
resolvers += "spray repo" at "http://repo.spray.io"

libraryDependencies ++= {
  val akkaVersion  = "2.3.12"
  val sprayVersion = "1.3.3"
  Seq(
    "com.typesafe.akka" %% "akka-actor"    % akkaVersion, 
    "io.spray"          %% "spray-can"     % sprayVersion,
    "io.spray"          %% "spray-routing" % sprayVersion
  )
}

Revolver.settings : Seq[sbt.Def.Setting[_]]
