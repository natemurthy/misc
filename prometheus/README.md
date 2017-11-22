# prometheus

A small example of running an app that exposes a prometheus metrics endpoint on
port `8081` with a telegraf sidecar that pulls from the prometheus client and saves
measurements in influxdb.

### Usage
```
$ docker-compose upi --abort-on-container-exit
```
Clean up:
```
docker rm pythonprometheus_app_1 pythonprometheus_telegraf_1 pythonprometheus_influxdb_1
```

