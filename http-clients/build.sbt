name := "http-clients"

scalaVersion := "2.11.6"

libraryDependencies ++= Seq(
  "com.typesafe.play"         %% "play-ws"        % "2.4.2",
  "com.typesafe.play"         %% "play-iteratees" % "2.4.2",
  "org.glassfish.jersey.core" % "jersey-client"   % "2.19"
)
 
