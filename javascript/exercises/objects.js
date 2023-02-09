
function Movie(title, director, writer, releaseDate, mpaaRating) {
  // object parameters
  this.title = title;
  this.director = director;
  this.writer = writer;
  this.releaseDate = releaseDate;
  this.mpaaRating = mpaaRating;
  
  // class methods
  this.trailer = trailer;
  this.audience = audience;
}

function trailer() {
  return `${this.title}, written by ${this.writer} and directed by ${this.director}, will be released on ${this.releaseDate}.`;
};

function audience() {
  switch(this.mpaaRating) {
    case 'R':
      return "For audiences above the age of 16";
    case 'PG-13':
      return "For audiences above the age of 12";
    case 'PG':
      return "Parental guidance suggested";
    case 'G':
      return "For general audiences"; 
    };
};

var movies = [
  new Movie("Hacked", "Issae Rae", "Amber Hall", 2025, "R"),
  new Movie("Nutty Professor", "Tom Shadyac", "Jerry Lewis", 1996, "PG-13"),
  new Movie("Shrek", "Andrew Adamson", "Ted Elliott", 2001, "PG"),
  new Movie("The Wizard of Oz", "Victor Fleming", "L. Frank Baum", 1939, "G")
]

for (let i = 0; i < movies.length; i++) {
  let m = movies[i]
  console.log('');
  console.log(m.trailer());
  console.log(m.audience());
  console.log('');
}

