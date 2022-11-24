let people = {"tom": 34, "jane": 68, "amber": 26}

// access
console.log(people["amber"])

// delete
delete people["tom"]
console.log(people)

// insert
people.henry = 18
people["nug'get"] = 7
console.log(people)

// search
for (const [k,v] of Object.entries(people)) {
  if (v < 10) {
    console.log(k, v)
  }
}
