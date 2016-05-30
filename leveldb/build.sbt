import sbt._
import Keys._


scalaVersion in ThisBuild := "2.11.8"

lazy val myProject = Project(
    id = "myProject",
    base = file("."),
    settings = Defaults.defaultSettings ++ 
      Seq(mainRunNobootcpSetting, testRunNobootcpSetting)
  )

  val runNobootcp =
    InputKey[Unit]("run-nobootcp", "Runs main classes without Scala library on the boot classpath")

  val mainRunNobootcpSetting = runNobootcp <<= runNobootcpInputTask(Runtime)
  val testRunNobootcpSetting = runNobootcp <<= runNobootcpInputTask(Test)

  def runNobootcpInputTask(configuration: Configuration) = inputTask {
    (argTask: TaskKey[Seq[String]]) => (argTask, streams, fullClasspath in configuration) map { (at, st, cp) =>
      val runCp = cp.map(_.data).mkString(java.io.File.pathSeparator)
      val runOpts = Seq("-classpath", runCp) ++ at
      val result = Fork.java.fork(None, runOpts, None, Map(), false, LoggedOutput(st.log)).exitValue()
      if (result != 0) error("Run failed")
    }
  }

libraryDependencies ++=  
Seq(
  "org.iq80.leveldb"          % "leveldb"            % "0.7",
  "org.fusesource.leveldbjni" % "leveldbjni-linux64" % "1.8"
)
