name := "jetty-websocket"

version := "1.0-SNAPSHOT"

scalaVersion := "2.11.6"

libraryDependencies ++= Seq(
  "org.eclipse.jetty.websocket" % "websocket-client" % "9.3.1.v20150714",
  "joda-time"                %  "joda-time"           % "2.8.1",
  "org.json4s"               %% "json4s-jackson"      % "3.2.11"
)

