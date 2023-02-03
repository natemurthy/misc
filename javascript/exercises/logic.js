/*
Pretend you are working on a website, and need to implement the functionality to make sure users pick strong passwords. Given the variable "password" write some code to return a helpful error message as an `alert()` if the user does not meet the password requirements and let them know WHY it did not meet the requirement.

The password must be:

Between 10 and 15 characters

Include at least 1 special character (*, $, &, !, @, or +)

Have at least 1 capital letter?

Have at least 1 lowercase letter?

Have the number 1 as the fifth character of the password

*/

let password = ""

//YOUR CODE GOES HERE.
//Fill in the password variable for testing
function isPasswordValid(str) {
  const prefix = "Password must ";
  if (str.length < 10 || str.length > 15) {
    alert(prefix+"be between 10 and 15 characters");
    return;
  }
  if (!/[*$&!@+$]/.test(str)) {
    alert(prefix+"include at least 1 special character (*, $, &, !, @, or +)");
    return;
  }
  if (!/[A-Z]/.test(str)) {
    alert(prefix+"have at least 1 capital letter");
    return;
  }     
  if (!/[a-z]/.test(str)) {
    alert(prefix+"have at least 1 lowercase letter");
    return;
  }
  if (str[4]!="1") {
    alert(prefix+"have the number 1 as the fifth character");
    return;
  }
  alert("Congrats! You have a valid password!");
}

isPasswordValid("short"); // Cannot be less than 10 characters
isPasswordValid("longlongreallylongpassword") // Cannot be greater than 15 characters
isPasswordValid("foobarbazsqipp"); // Missing at least 1 special character
isPasswordValid("foobarbaz*qipp"); // Missing at least 1 uppercase letter
isPasswordValid("FOOBARBAZ*QIPP"); // Missing at least 1 lowercase letter 
isPasswordValid("FooBarbaz*qipp"); // Missing number 1 as he fifth character
isPasswordValid("FooB1baz*bqipp"); // Success

