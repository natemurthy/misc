import com.typesafe.sbt.packager.docker._

name := "clustering"

organization := "com.mlh"

version := "0.3"

homepage := Some(url("https://github.com/mhamrah/clustering"))

startYear := Some(2013)

scmInfo := Some(
  ScmInfo(
    url("https://github.com/mhamrah/clustering"),
    "scm:git:https://github.com/mhamrah/clustering.git",
    Some("scm:git:git@github.com:mhamrah/clustering.git")
  )
)

/* scala versions and options */
scalaVersion := "2.11.8"

// These options will be used for *all* versions.
scalacOptions ++= Seq(
  "-deprecation"
  ,"-unchecked"
  ,"-encoding", "UTF-8"
  ,"-Xlint"
  ,"-Yclosure-elim"
  ,"-Yinline"
  ,"-Xverify"
  ,"-feature"
  ,"-language:postfixOps"
)

val akka = "2.4.13"

/* dependencies */
libraryDependencies ++= Seq (
  "com.github.nscala-time" %% "nscala-time" % "1.2.0"
  // -- testing --
  , "org.scalatest" %% "scalatest" % "2.2.6" % "test"
  // -- Logging --
  ,"ch.qos.logback" % "logback-classic" % "1.1.7"
  // -- Akka --
  ,"com.typesafe.akka" %% "akka-testkit" % akka % "test"
  ,"com.typesafe.akka" %% "akka-actor" % akka
  ,"com.typesafe.akka" %% "akka-slf4j" % akka
  ,"com.typesafe.akka" %% "akka-cluster" % akka
  // -- json --
  ,"org.json4s" %% "json4s-jackson" % "3.3.0"
  // -- config --
  ,"com.typesafe" % "config" % "1.3.0"
)

dockerRepository := Some("nmurthy")
dockerCommands := Seq(
  Cmd("FROM", "openjdk:8-jre-alpine"),
  Cmd("WORKDIR","/opt/docker"),
  Cmd("ADD","opt /opt"),
  Cmd("EXPOSE","1600"),
  Cmd("RUN","apk add --update bash && rm -rf /var/cache/apk/*"),
  ExecCmd("ENTRYPOINT","sh", "-c", "CLUSTER_IP=`/sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1 }'` bin/clustering $*")
)

enablePlugins(JavaAppPackaging)
