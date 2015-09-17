import info.BuildInfo

object Main extends App {
  println(s"${BuildInfo.name} v${BuildInfo.version}")
}