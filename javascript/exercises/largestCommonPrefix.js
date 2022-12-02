/*
 * https://leetcode.com/problems/longest-common-prefix/
 *
 * Write a function to find the longest common prefix string amongst an array of strings.
 * If there is no common prefix, return an empty string "".
 *
 * Constraints:
 *   1 <= strs.length <= 200
 *   0 <= strs[i].length <= 200
 *   strs[i] consists of only lowercase English letters
*/
const test1 = ["flower","flow","flight","four"]

const test2 = ["dog","racecar","car"]

const test3 = ["unlikely", "unlike", "unlovable", "unlucky", "unified"]

function getPrefixes(str) {
  let output = []
  for (let j = 0; j <= str.length; j++) {
    output.push(str.substring(0, j))
  }
  return output
}

function find1(arr) {
  let allPrefixes = []
  for (let i = 0; i < arr.length; i++) {
    let w = arr[i]
    allPrefixes.push(getPrefixes(w))
  }

  let result = ''
  for (let i = 0; i < allPrefixes.length-1; i++) {
    let curPrefixes = allPrefixes[i]
    for (let j = 0; j < curPrefixes.length; j++) {
      if (allPrefixes[i][j] == allPrefixes[i+1][j]) {
        result = allPrefixes[i][j]
        //console.log(result)
      }
    }
  }
  return result
}

lcp = find1(test3)

console.log("")
console.log("find1 solution:", lcp)

function find2(arr) {
  let allPrefixes = {}
  arr.forEach( w => { 
    getPrefixes(w).forEach( k => {
      if (k in allPrefixes) {
        c = allPrefixes[k]++
      } else {
        allPrefixes[k] = 1
      }
    })
  })

  let maxCount = 0
  let candidatePrefixes = []
  for (const [k,v] of Object.entries(allPrefixes)) {
    if (v >= maxCount) {
      maxCount = v
      candidatePrefixes.push(k)
    }
  }
  return candidatePrefixes.slice(-1)[0]
}

lcp = find2(test3)

console.log("")
console.log("find2 solution:", lcp)


