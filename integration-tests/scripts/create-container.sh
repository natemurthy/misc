docker build -f Dockerfile.orientdb -t orientdb .
docker run -ti -v `pwd`/databases:/orientdb/databases -p 2424:2424 -p 2480:2480 orientdb
