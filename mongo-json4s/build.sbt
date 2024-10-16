name := "mongo-json4s"

version := "1.0"

scalaVersion in ThisBuild := "2.11.8"

libraryDependencies ++= Seq(
  "org.json4s" %% "json4s-jackson" % "3.2.11",
  "org.json4s" %% "json4s-mongo" % "3.2.11",
  "org.mongodb" % "mongo-java-driver" % "3.0.3"
  )
  
