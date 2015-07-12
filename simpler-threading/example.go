package main

import "time"

func publishDgmsStatus() {
  // read and publish some state from the DB
  pubsubClient.publishMessage(status)
}

func updateDynamicSetpoints() {
  // solve and publish updated dynamic setpoints
  result := Solver.solve().withAlgorithm(algoType)
  pubsubClient.publishMessage(result)
}

func shutoffInverters() {
  // assign which inverters to shutoff
  pubsubClient.publishMessage(zeroSetpoints)
}


func main() {
    statusPublisher   := time.Tick(5 * time.Second)
    setpointPublisher := time.Tick(5 * time.Minute)
    currentNetLoad := <-pubsubClient.measurementChannel
    for {
        select {
        case <-statusPublihser:
           publishDgmsStatus() 
        case <-setpointPublihser:
           updateDynamicSetpoints()
        case <-currentNetLoad:
            if (currentNetLoad < pccImportBand(1) and isWithinShutoffWindow) shutoffInverters()
        }
    }
}
