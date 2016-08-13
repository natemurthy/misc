import Dependencies._
import sbt._

name := "app-name"

lazy val commonSettings = Seq(
  // build settings
  scalaVersion in ThisBuild := "2.11.8",
  organization in ThisBuild := "natemurthy",

  // test settings
  parallelExecution in Test := false,
        javaOptions in Test ++= Seq(
          "-Dconfig.file=conf/application.test.conf",
          "-Dlogger.file=conf/logback-test.xml"
        ),
  coverageExcludedPackages := """controllers.docs;controllers\..*Reverse.*;router.Routes.*;""" +
    "pl.matisoft.swagger; pl.matisoft.swagger.javascript; views.html",
    
  // classpaths and dependencies
  scriptClasspath := Seq("../conf/","*"),
  libraryDependencies ++= Seq(
    "org.scalatest"    %% "scalatest" % scalaTestVersion % "test"
  )
)

lazy val common = (project in file("common")).settings(commonSettings)

lazy val `service-a` = (project in file("services/service-a"))
                         .enablePlugins(PlayScala)
                         .dependsOn(common)
                         .settings(commonSettings)

lazy val `service-b` = (project in file("services/service-b"))
                         .enablePlugins(PlayScala)
                         .dependsOn(common)
                         .settings(commonSettings)
