package controllers

import com.github.tototoshi.play2.json4s.jackson._
import org.json4s._
import org.json4s.JsonDSL._
import play.api.mvc._


object Application extends Controller with Json4s {

  implicit val formats = DefaultFormats

  def getStatus = Action {
    val response: JValue = "DgmsInstanceId"->"dgms-service-0000"
    Ok(response)
  }

}
