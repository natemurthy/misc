import akka.actor._

class DgmsService extends Actor {
  val pubsubClient = PubsubClientActor()
  val statusPublisher   = context.scheduler.schedule(5.seconds) { publishDgmsStatus() }
  val setpointPublihser = context.scheudler.schedule(5.minutes) { updateDynamicSetpoints() }

  def publishDgmsStatus() = {
    // read and publish some state from the DB
    pubsubClient ! PublishMessage(status)
  }

  def updateDynamicSetpoints() = {
    // solve and publish updated dynamic setpoints
    val result = Solver.solve().withAlgorithm(algoType)
    pubsubClient ! PublishMessage(result)
  }

  def shutoffInverters() = {
    // assign which inverters to shutoff
    pubsubClient ! PublishMessage(zeroSetpoints)
  }

  def receive = {
    case NetLoadMeasurement(currentNetLoad) =>
      if (currentNetLoad < pccImportBand(1) and isWithinShutoffWindow) shutoffInverters()
  }

}
