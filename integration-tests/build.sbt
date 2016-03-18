import sbt._
import Keys._

name := "integration-tests"
version := "1.0"
scalaVersion in ThisBuild := "2.11.7"

coverageMinimum := 75
coverageFailOnMinimum := true

libraryDependencies ++=
Seq(
  "com.thenewmotion.akka" %% "akka-rabbitmq"    % "2.2",
  "com.orientechnologies" %  "orientdb-graphdb" % "2.1.4",
  "org.scalatest"         %% "scalatest"        % "2.2.6" % "test"
)

resolvers += "The New Motion Public Repo" at "http://nexus.thenewmotion.com/content/groups/public/"

logLevel in Global := Level.Warn

lazy val root = (project in file("."))
				  .configs(IntegrationTest)
				  .settings(integrationTestSettings)
          .settings(testSettings)

lazy val formattingTestArg = Tests.Argument("-eDFG")

lazy val integrationTestSettings = inConfig(IntegrationTest)(Defaults.testTasks) ++
    Seq(
      testOptions in IntegrationTest := Seq(formattingTestArg, Tests.Argument("-n", "integration"))
    )

lazy val testSettings = Seq(
    testOptions in Test := Seq(formattingTestArg, Tests.Argument("-l", "integration")),
    parallelExecution in Test := false,
    fork in Test := true
  )

lazy val IntegrationTest = config("integration") extend Test

assemblyMergeStrategy in assembly := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case _ => MergeStrategy.first
}
