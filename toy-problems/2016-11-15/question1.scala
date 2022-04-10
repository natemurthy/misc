/**
 *  input: list of integers
 * output: count of all non-zero integers
 *         move all zeros to tail
 **/

var xs = List(1, 2, 3, -4, 0, 0, 2, 4, 0)

def moveZerosToTailAndCountNonZeros: Int = {
  val nonZeros = xs.filter(_ != 0)
  xs = xs.filter(_ != 0) ++ xs.filter(_ == 0)
  nonZeros.size
}
