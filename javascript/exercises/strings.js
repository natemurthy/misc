/* Go through the following examples and log the proper output to the console. DO NOT edit the variables provided */

/*
1. Use a string method to check if the "test1" variable contains the contents of the "test2" variable. If it does, log "test1 contains here" to the console. If not log "test1 does not contain here" to the console
*/


var test1 = "asjsdfhereasdasd";
var test2 = "here";
//YOUR CODE GOES HERE
if (test1.includes(test2)) {
  console.log("test1 contains here");
} else {
  console.log("test1 does not contain here");
}


/* 
2. Write some code to determine if a variable contains the letters "a", "b", and "c". They do not need to be in order in the variable as long as it contains them all. If all three letters are present in a variable log "Success" to the console. If a variable does not contain all the letters, log which letter(s) are missing in the console.

Use "randomString1", "randomString2", "randomString3", and "randomString4" to test your code and log each result to the console.
*/

var randomString1 = "asfdsafngdicsdfb"

var randomString2 = "urjsfghbogjfdc"

var randomString3 = "sfurireogncefg"

var randomString4 = "irjordguogrdj"
//YOUR CODE GOES HERE
function determine(str) {
  console.log(`checking ${str}`);
  let has_a = str.includes("a");
  let has_b = str.includes("b");
  let has_c = str.includes("c");
  if (has_a && has_b && has_c) {
    console.log("Success");
  } else {
    if (!has_a) {
      console.log("missing letter 'a'");
    }
    if (!has_b) {
      console.log("missing letter 'b'");
    }
    if (!has_c) {
      console.log("missing letter 'c'");
    }
  }
}
determine(randomString1);
determine(randomString2);
determine(randomString3);
determine(randomString4);

/* 3. 
Use a string method to replace the final word of the "bestSuperhero" variable with your favorite superhero and log the new output to the console
*/

var bestSuperhero = "The best Super Hero is Thanos"
//YOUR CODE GOES HERE
function replaceHero(best, newHero) {
  let arr = best.split(' ');
  arr.pop();
  arr.push(newHero); 
  console.log(arr.join(' ')); 
}
replaceHero(bestSuperhero, 'NUGGET!');

/* 4. 
Use a string method to make the variable "replacementSentence" say "Val is a great ITA instructor". Log the contents of the updated "replacementSentence" to the console
*/

var replacementSentence = "Mark is an average ITA instructor."
//YOUR CODE GOES HERE
console.log(replacementSentence.replace("an average", "a great"));

/* 5. 
Write some code that will always replace the final word in a sentence with the string "hotdog". Make sure it works on all of the "sentence" variables provided. 
*/

var sentence1 = "I want to go visit Paris"

var sentence2 = "I love to debug my code with a proper debugger."

var sentence3 = "Writing code is fun! "

//YOUR CODE GOES HERE
function replaceFinalWord(sentence, word) {
  let trimmed = sentence.trim();
  let arr = trimmed.split(' ');
  const lastElement = arr.pop();
  const lastChar = lastElement[lastElement.length-1];
  const isPunctuation = !(/[a-zA-Z]/).test(lastChar)
  if (isPunctuation) {
    arr.push(word+lastChar);
  } else {
    arr.push(word);
  }
  console.log(arr.join(' '));
}
replaceFinalWord(sentence1, "hotdog");
replaceFinalWord(sentence2, "hotdog");
replaceFinalWord(sentence3, "hotdog");

