name := "oassg-orientdb"

scalaVersion in ThisBuild := "2.11.6"

scalacOptions in ThisBuild ++= Seq("-unchecked", "-deprecation", "-feature")

libraryDependencies ++= Seq(
  "com.orientechnologies" %  "orientdb-graphdb" % "2.1.0",
  "com.jsuereth"          %% "scala-arm"        % "1.4"
)
