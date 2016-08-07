name := "sdbc-example"

version := "0.1-SNAPSHOT"

scalaVersion in ThisBuild := "2.11.8"

libraryDependencies ++= Seq(
  "com.jsuereth" %% "scala-arm"       % "1.4",
  "com.wda.sdbc" %% "sqlserver-java7" % "0.10"
)
