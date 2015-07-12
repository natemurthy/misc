using System;
using System.Diagnostics;
using System.Threading;

public class Seq 
{
   public static void Countdown(int n)
   {
      while (n>0)
         n -= 1;
   }

   public static void Main(string[] args)
   {
      int COUNT = 80000000;
      Stopwatch stopWatch = new Stopwatch();
      stopWatch.Start();
      Countdown(COUNT);
      stopWatch.Stop();
      TimeSpan ts = stopWatch.Elapsed;
      Console.WriteLine(ts);
   }
}
