// 1. Write a function that would allow you to do this:

function exercise(str) {
        return function today() {
                return `Today's exercise: ${str}`;
        }
}

var swim = exercise("swim");

var run = exercise("run");

console.log(swim());
// Today's exercise: swim 
console.log(run());
// Today's exercise: run


// 2. Write a function that would allow you to do this:

function cutPizzaSlices(n) {
        return function splitPizza(p) {
                //let s = (n/p).toFixed(2);
                let s = n/p;
                return `Each person gets ${s} slices`;
        }
}
var sharePizza = cutPizzaSlices(8);
console.log(sharePizza(2));
console.log(sharePizza(3));


// 3. - Data Security: Using your knowledge of scoping, create an object called 
//       pii (Personally Identifiable Information) that cannot be accessed directly. 
//       The object should have at least two properties: name and ssn.
//       Only the name property should be accessible, 
//       and it should be called through a public function.
//       The ssn property should not be accessible at all.

//       Creating private objects and private properties helps you control 
//       who has access to what data and helps you prevent people who 
//       shouldn't see important info like social security numbers 
//       from getting access to the data.
//       You can use 'getName' or other get methods to access data that 
//       people might need. For example, people addressing a package 
//       or email may need a customer's name, but they definitely 
//       shouldn't have access to their ssn.


class Dinosaur{
    #name = ''; // Private fields need to be declared
    #milYears = 0;
  
    constructor(name, milYears, region) {
        this.#name = name;
        this.region = region;
        this.#milYears = milYears;
    }
}
dino = new Dinosaur('Euhelopus', 100.5, 'Asia');
console.log(dino.region)
//console.log(dino.#milYears)
//console.log(dino.#name)





class Person {
        #ssn;

        constructor(name, ssn) {
                this.name = name;
                this.#ssn = ssn;
        }

        // optional
        getName() {
                return this.name;
        }
}

p = new Person("Amber Hall", "123456789");
console.log(p);
console.log(p.name);
console.log(p.getName());
console.log(p.ssn);

