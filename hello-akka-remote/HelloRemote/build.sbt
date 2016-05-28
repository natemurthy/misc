name := "hello-remote"

resolvers += "Typesafe Repository" at "http://repo.typesafe.com/typesafe/releases/"

libraryDependencies ++= Seq(
  "com.typesafe.akka" %% "akka-actor"  % "2.3.10",
  "com.typesafe.akka" %% "akka-remote" % "2.3.10"
)

