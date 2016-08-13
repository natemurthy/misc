package controllers

import javax.inject._
import play.api._
import play.api.mvc._


@Singleton
class ServiceB @Inject() extends Controller {

  def ping = Action {
    Ok("Service B: pong")
  }

}
