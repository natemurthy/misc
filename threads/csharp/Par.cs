using System;
using System.Diagnostics;
using System.Threading;

public class Counter
{
   int n;
   public Counter(int count)
   {
      n = count;
   }
   public void Countdown()
   {
      while (n>0)
         n -= 1;
   }
}

public class Par
{
   public static void Main(string[] args)
   {
      int COUNT = 80000000;
      Counter c1 = new Counter(COUNT/2);
      Counter c2 = new Counter(COUNT/2); 
      Thread t1 = new Thread(new ThreadStart(c1.Countdown));
      Thread t2 = new Thread(new ThreadStart(c2.Countdown));
      Stopwatch stopWatch = new Stopwatch();
      stopWatch.Start();
      t1.Start(); t2.Start();
      //t1.Join(); t2.Join();
      stopWatch.Stop();
      TimeSpan ts = stopWatch.Elapsed;
      Console.WriteLine(ts);
   }
}
