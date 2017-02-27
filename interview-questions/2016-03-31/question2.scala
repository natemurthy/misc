// Question 2

def fibonacci(n:Int): Int = {
  def fibTail(n:Int, a:Int, b:Int): Int = n match {
    case 0 => a
    case _ => fib_tail( n-1, b, a+b )
  }
  return fibTail( n, 0, 1)
}

def factorial(n:Int): Int = {
  if (n == 1) 1
  else n*factorial(n-1)
}

@tailrec
def factorial(num:Int) = {
  def factWithAccum(acc:Int, n:Int): Int = {
    if (n==0) acc
    else factWithAccum(acc*n,n-1)
  }
  factWithAccum(1,num)
}
