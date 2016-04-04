name := "protobuf-examples"

val V = "3.0.0-beta-2"

libraryDependencies ++= Seq(
  "com.google.protobuf" % "protobuf-java"      % V,
  "com.google.protobuf" % "protobuf-java-util" % V,
  "com.googlecode.protobuf-java-format" % "protobuf-java-format" % "1.4"
)

