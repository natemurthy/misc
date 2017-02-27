public class sleep {

    public static void main(String [] args) {
        int millis = Integer.parseInt(args[0]);
	try {
	    Thread.sleep(millis);
	} catch (InterruptedException e) {
	    System.out.println(e.getMessage());
	}
    }
}
