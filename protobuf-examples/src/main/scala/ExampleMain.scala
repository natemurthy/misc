import examples.AddressBookProtos._ 

object ExampleMain extends App {

val p = Person.newBuilder().setId(123).setName("John").addPhone(Person.PhoneNumber.newBuilder().setNumber("555-1234").setType(Person.PhoneType.HOME)).build()

// using com.google.protobuf
def scope1 = {

import com.google.protobuf.util._

val js1 = JsonFormat.printer().print(p)
var p1 = Person.newBuilder()
JsonFormat.parser().merge(js1,p1)

}


// using com.googlecode.protobuf
def scope2 = {

import com.googlecode.protobuf.format._
import com.googlecode.protobuf.format.FormatFactory.Formatter
import com.googlecode.protobuf.format.util.TextUtils

val jsFmt = new FormatFactory().createFormatter(Formatter.JSON)
val js2 = jsFmt.printToString(p)
var p2 = Person.newBuilder()
jsFmt.merge(TextUtils.toInputStream(js2), p2)

}

}
