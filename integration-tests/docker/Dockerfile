# Pull base image.
FROM ubuntu

COPY . /myapp
WORKDIR /myapp

# Install Sun JDK 8
RUN \
  echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && \
  add-apt-repository -y ppa:webupd8team/java && \
  apt-get update && \
  apt-get install -y oracle-java8-installer && \
  rm -rf /var/lib/apt/lists/* && \
  rm -rf /var/cache/oracle-jdk8-installer && \
  apt-get clean && \
  eval $(sed s/sbt.version/SBT_VERSION/ </myapp/project/build.properties) && \
  mkdir -p /usr/local/bin && \
  wget -P /usr/local/bin/ http://repo.typesafe.com/typesafe/ivy-releases/org.scala-sbt/sbt-launch/$SBT_VERSION/sbt-launch.jar && \
  cp /myapp/project/sbt /usr/local/bin && chmod +x /usr/local/bin/sbt && \
  ... sbt assembly

# Define commonly used JAVA_HOME variable
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

ENTRYPOINT ["./bin/start"]
