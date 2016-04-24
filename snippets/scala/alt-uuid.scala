// see: http://stackoverflow.com/questions/41107/how-to-generate-a-random-alpha-numeric-string

import java.security.SecureRandom, java.math.BigInteger

val random = new SecureRandom()
new BigInteger(130, random).toString(32)
