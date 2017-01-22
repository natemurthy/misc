public class par {

    static void countdown(int n) {
    	while (n > 0) { n -= 1; }
	//System.out.println(n);
    }
	
    public static void main(String [] args) {
        final int COUNT = 80000000;
        Thread t1 = new Thread() {
            public void run() { countdown(COUNT/2); }
        };
        Thread t2 = new Thread() {
            public void run() { countdown(COUNT/2); }
        };
        long start = System.nanoTime();
        t1.start(); t2.start();
        //try { t1.join(); t2.join(); } catch (InterruptedException e) { System.out.println(e); }
        long end = System.nanoTime();
        System.out.println("elapsed time = " + (end-start) + " nanoseconds");
    }
}
