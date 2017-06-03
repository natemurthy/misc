lazy val commonSettings = Seq(
  organization := "com.bigcommerce",
  version := "0.1.0",
  scalaVersion := "2.12.2"
)

val GRPC_VERSION = "1.3.0"
val SCALAPB_VERSION = com.trueaccord.scalapb.compiler.Version.scalapbVersion

lazy val interfaces =
  (project in file("interfaces"))
    .settings(commonSettings)
    .settings(watchSources ++= ((baseDirectory.value / "src" / "main" / "protobuf") ** "*.proto").get)
    .settings(libraryDependencies ++= Seq(
    	"io.grpc" % "grpc-stub" % GRPC_VERSION,
    	"com.trueaccord.scalapb" %% "scalapb-runtime" % SCALAPB_VERSION % "protobuf",
    	"com.trueaccord.scalapb" %% "scalapb-runtime-grpc" % SCALAPB_VERSION
    ))
    .settings(PB.targets in Compile := Seq(
  		scalapb.gen(flatPackage = false) -> (sourceManaged in Compile).value
		))

lazy val root = Project(id = "fortune", base = file("."))
    .settings(commonSettings: _*)
    .settings(libraryDependencies ++= Seq(
    	"io.grpc" % "grpc-netty" % GRPC_VERSION,
      "com.typesafe.akka" %% "akka-actor" % "2.5.2"
    ))
    .dependsOn(interfaces)
