import static org.junit.Assert.*;
import org.junit.Test;

public class SolutionTest {

    @Test
    public void testIsUniqueChars() {
         assertTrue( Solution.isUniqueChars("uniq") );
        assertFalse( Solution.isUniqueChars("non-unique") );
    }

}
