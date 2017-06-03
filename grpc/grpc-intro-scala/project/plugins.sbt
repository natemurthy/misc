resolvers += "Typesafe repository" at "http://repo.typesafe.com/typesafe/releases/"

libraryDependencies += "com.trueaccord.scalapb" %% "compilerplugin" % "0.6.0-pre4"

addSbtPlugin("com.thesamet" % "sbt-protoc" % "0.99.8")

addSbtPlugin("io.spray" % "sbt-revolver" % "0.8.0")