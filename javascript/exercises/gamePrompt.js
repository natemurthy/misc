/* As we have not yet covered functions, see if you can understand what the provided code does. We will cover this more in the following weeks. At a very high level, functions help us take the code you have already been writing, and bundle it into a little package that you can use over and over again without having to rewrite or change the code. 

Your game is going to play against the computer,so it begins with a function called computerPlay that will randomly return either ‘Rock’, ‘Paper’ or ‘Scissors’. We’ll use this function in the game to make the computer’s play.  There will be another function that plays a single round of Rock Paper Scissors. The function takes two parameters - the playerSelection and computerSelection - and should return a string that declares the winner of the round like so: ""You Lose! Paper beats Rock""

Make your playerSelection accept case insensitive inputs (so users can input rock, ROCK, RocK or any other variation)
*/


function computerPlay(){
  var computerOptions = ["rock", "paper", "scissors"]
  
  // Write code to select a random element from this array and return it as "randomSelection"
  
  const randomSelection // save the computers selection here
  return randomSelection
}

function playRound(playerSelection, computerSelection) {
  // Write code to compare player selection and computer selection and return the proper message.
  const finalMessage  = "" 
  return finalMessage
}


const playerSelection = ""
// update this to accept input from the user using prompt(). Make sure to handle different capitilizations in the input, and if the user provides unexpected input: i.e. something that is not some variation of "rock", "paper", or "scissors"

const computerSelection = computerPlay();
// dont change this, this runs the computer() code, to generate a computer selection

console.log(playRound(playerSelection, computerSelection))
// this will run the playRound code, with the playerSelection and computerSelection constants, and return and log the finalMessage variable!
