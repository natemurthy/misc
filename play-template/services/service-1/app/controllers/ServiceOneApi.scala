package controllers

import javax.inject._
import play.api._
import play.api.mvc._


@Singleton
class ServiceOneApi @Inject() extends Controller {

  def ping = Action {
    Ok("Service One API: pong")
  }

}
