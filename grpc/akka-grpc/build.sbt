// *****************************************************************************
// Projects
// *****************************************************************************

lazy val `akka-grpc` =
  project
    .in(file("."))
    .enablePlugins(GitVersioning)
    .aggregate(core, example)
    .settings(settings)
    .settings(
      unmanagedSourceDirectories.in(Compile) := Seq.empty,
      unmanagedSourceDirectories.in(Test) := Seq.empty,
      publishArtifact := false
    )

lazy val core =
  project
    .in(file("core"))
    .enablePlugins(AutomateHeaderPlugin)
    .disablePlugins(ProtocPlugin)
    .settings(settings)
    .settings(
      name := "akka-grpc",
      libraryDependencies ++= Seq(
        library.akkaStream,
        library.grpcNetty,
        library.grpcStub,
        library.scalaCheck % Test,
        library.scalaTest  % Test
      )
    )

lazy val example =
  project
    .in(file("example"))
    .enablePlugins(AutomateHeaderPlugin)
    .dependsOn(core)
    .settings(settings)
    .settings(pbSettings)
    .settings(
      name := "akka-grpc-example",
      publishArtifact := false
    )

// *****************************************************************************
// Library dependencies
// *****************************************************************************

lazy val library =
  new {
    object Version {
      val akka       = "2.5.1"
      val grpc       = "1.3.0"
      val scalaCheck = "1.13.4"
      val scalapb    = com.trueaccord.scalapb.compiler.Version.scalapbVersion
      val scalaTest  = "3.0.1"
    }
    val akkaStream         = "com.typesafe.akka"      %% "akka-stream"          % Version.akka
    val grpcNetty          = "io.grpc"                %  "grpc-netty"           % Version.grpc
    val grpcStub           = "io.grpc"                %  "grpc-stub"            % Version.grpc
    val scalaCheck         = "org.scalacheck"         %% "scalacheck"           % Version.scalaCheck
    val scalapbRuntimeGrpc = "com.trueaccord.scalapb" %% "scalapb-runtime-grpc" % Version.scalapb
    val scalaTest          = "org.scalatest"          %% "scalatest"            % Version.scalaTest
}

// *****************************************************************************
// Settings
// *****************************************************************************        |

lazy val settings =
  commonSettings ++
  scalafmtSettings ++
  gitSettings ++
  headerSettings

lazy val commonSettings =
  Seq(
    scalaVersion := "2.12.1",
    crossScalaVersions := Seq(scalaVersion.value, "2.11.8"),
    organization := "de.heikoseeberger",
    licenses += ("Apache 2.0",
                 url("http://www.apache.org/licenses/LICENSE-2.0")),
    mappings.in(Compile, packageBin) +=
      baseDirectory.in(ThisBuild).value / "LICENSE" -> "LICENSE",
    scalacOptions ++= Seq(
      "-unchecked",
      "-deprecation",
      "-language:_",
      "-target:jvm-1.8",
      "-encoding", "UTF-8"
    ),
    javacOptions ++= Seq(
      "-source", "1.8",
      "-target", "1.8"
    ),
    unmanagedSourceDirectories.in(Compile) :=
      Seq(scalaSource.in(Compile).value),
    unmanagedSourceDirectories.in(Test) :=
      Seq(scalaSource.in(Test).value)
)

lazy val scalafmtSettings =
  reformatOnCompileSettings ++
  Seq(
    formatSbtFiles := false,
    scalafmtConfig :=
      Some(baseDirectory.in(ThisBuild).value / ".scalafmt.conf"),
    ivyScala :=
      ivyScala.value.map(_.copy(overrideScalaVersion = sbtPlugin.value)) // TODO Remove once this workaround no longer needed (https://github.com/sbt/sbt/issues/2786)!
  )

lazy val gitSettings =
  Seq(
    git.useGitDescribe := true
  )

import de.heikoseeberger.sbtheader.HeaderPattern
import de.heikoseeberger.sbtheader.license.Apache2_0
lazy val headerSettings =
  Seq(
    headers := Map("scala" -> Apache2_0("2017", "Heiko Seeberger"))
  )

lazy val pbSettings =
  Seq(
    PB.protoSources.in(Compile) :=
      Seq(sourceDirectory.in(Compile).value / "proto"),
    PB.targets.in(Compile) :=
      Seq(scalapb.gen() -> sourceManaged.in(Compile).value),
    libraryDependencies ++= Seq(
      library.scalapbRuntimeGrpc
    )
  )
