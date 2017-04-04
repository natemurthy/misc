#include <stdio.h>
#include <string.h>


// The checksum at the end of each sentence is the XOR of all of the bytes in the sentence, 
// excluding the initial dollar sign. The following C code generates a checksum for the 
// string entered as "mystring" and prints it to the output stream. In the example, a 
// sentence from the sample file is used.

int checksum(const char *s) {
    int c = 0;

    while(*s)
        c ^= *s++;

    return c;
}

int main()
{
    char mystring[] = "GPRMC,092751.000,A,5321.6802,N,00630.3371,W,0.06,31.66,280511,,,A";

    printf("String: %s\nChecksum: 0x%02X\n", mystring, checksum(mystring));

    return 0;
}
