/* Go through the following examples and log the proper output to the console. DO NOT edit the arrays provided */


/* 
1. Given the array "letters", use an array method to add the letter "d" to the end of the array and log the ouput to the console
 */

var letters = ["a", "b", "c"]
//YOUR CODE HERE
letters.push("d");
console.log(letters);

/* 
2. Given the array "letters2" use an array method to remove the last value from the array and log the output to the console
*/
var letters2 = ["a", "b", "c", "d", "f"]
//YOUR CODE HERE
letters2.pop();
console.log(letters2);

/* 3. Given the array "letters3" use an array method the remove the incorrect value (g) from the array and log the output to the console*/

var letters3 = ["a", "b", "c", "g", "d", "e"]
//YOUR CODE HERE
function remove_g(arr) {
  const i = arr.indexOf("g");
  if (i > -1) {
    arr.splice(i, 1);
  }
  console.log(arr);
}
remove_g(letters3);



/* 4. Given the array "letters4" use an array method to sort the array in alphabetical order and then log the output to the console */

var letters4 = ["g", "y", "f", "e", "a", "q", "r"]
//YOUR CODE HERE
console.log(letters4.sort());


/* 5. Given the array "letters5" use a combination of array method to sort the array in REVERSE alphabetical order and then log the output to the console */
var letters5 = ["g", "y", "f", "e", "a", "q", "r"]
//YOUR CODE HERE
console.log(letters5.sort().reverse());


/* 6. Given the array animals, use an array method to remove the plants from the array, and add in "bears" and "sharks". Log the output to the console */

var animals = ["bees", "lions", "cucumbers", "pineapples", "apples", "butterflies", "deer"]
//YOUR CODE HERE
for (let i = 0; i < animals.length; i++) {
  let w = animals[i];
  if (w == "cucumbers" || w == "pineapples" || w == "apples") {
    animals.splice(i, 1);
    i -= 1
  }
}
animals.push("bears");
animals.push("sharks");
console.log(animals);

/* 
7. Given the two arrays "fruits" and "vegetables" use an array method two combine the two arrays into a new array. Then use an array method to print out whether the new array includes the item "apple"
*/

var fruits = ["apple", "banana", "pineapple", "watermelon"]

var vegetables = ["carrot", "celery", "onion"]
//YOUR CODE HERE
var newArray = fruits.concat(vegetables);
console.log(newArray.includes("apple"));


/* 8. Given the array "numbers" use an array method to remove all the duplicate items in the array. You will likely need to do some research to get this one */

var numbers = [1, 3, 5, 6, 5, 7, 9, 11, 5, 6, 8, 3, 1]
//YOUR CODE HERE
//Research: https://stackoverflow.com/questions/9229645/remove-duplicate-values-from-js-array
console.log([...new Set(numbers)]);

