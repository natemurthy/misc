name := "hello-alpakka"

version := "0.1"
scalaVersion := "2.12.6"
sbtVersion := "1.2.1"

libraryDependencies ++= Seq(
  "ch.qos.logback"    %  "logback-classic"   % "1.2.3",
  "com.typesafe"      %  "config"            % "1.3.1",
  "com.typesafe.akka" %% "akka-slf4j"        % "2.5.16",
  "com.typesafe.akka" %% "akka-stream-kafka" % "0.22"
)

assemblyMergeStrategy in assembly := {
  case PathList("reference.conf") => MergeStrategy.concat
  case PathList("scalastyle-config.xml", xs @ _*) => MergeStrategy.discard
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x => (assemblyMergeStrategy in assembly).value(x)
}
