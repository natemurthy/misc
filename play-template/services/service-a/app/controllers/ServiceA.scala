package controllers

import javax.inject._
import play.api._
import play.api.mvc._


@Singleton
class ServiceA @Inject() extends Controller {

  def ping = Action {
    Ok("ServiceA: pong")
  }

}
