import sbt._

version := "1.0"

libraryDependencies ++=  
Seq(
  "org.iq80.leveldb"          % "leveldb"         %  "0.7"  %  "optional;provided",
  "org.fusesource.leveldbjni" % "leveldbjni-all"  %  "1.8"  %  "optional;provided"
)
