name := "oassg-orientdb"

scalaVersion in ThisBuild := "2.11.6"

libraryDependencies ++= Seq(
  "com.orientechnologies" %  "orientdb-graphdb" % "2.1.0",
  "com.jsuereth"          %% "scala-arm"        % "1.4"
)
