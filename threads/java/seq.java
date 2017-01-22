public class seq {

    static void countdown(int n) {
    	while (n > 0) { n-=1; }
    }
	
    public static void main(String [] args) {
        final int COUNT = 80000000;
        long start = System.nanoTime();
	countdown(COUNT);
        long end = System.nanoTime();
        System.out.println("elapsed time = " + (end-start) + " nanoseconds");
    }
}
