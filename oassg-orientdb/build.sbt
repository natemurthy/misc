name := "oassg-orientdb"

scalaVersion in ThisBuild := "2.11.8"

scalacOptions in ThisBuild ++= Seq("-unchecked", "-deprecation", "-feature")

libraryDependencies ++= Seq(
  "com.orientechnologies" %  "orientdb-graphdb" % "2.1.1",
  "com.jsuereth"          %% "scala-arm"        % "1.4",
  "org.json4s"            %% "json4s-jackson"   % "3.2.11"
)
