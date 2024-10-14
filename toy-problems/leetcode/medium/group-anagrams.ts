// https://leetcode.com/problems/group-anagrams/submissions/946255506/

function groupAnagrams(strs: string[]) {
        
        let anagramMap = new Map<string, Array<string>>();

        for (var s of strs) {
                const sortedStr = s.split('').sort().join('')
                let maybeValue = anagramMap.get(sortedStr)
                if (maybeValue == undefined) {
                        anagramMap.set(sortedStr,  [s])
                } else {
                        anagramMap.set(sortedStr, maybeValue.concat([s]))
                }
        }

        return Array.from(anagramMap.values())
}

console.log(groupAnagrams(["eat","tea","tan","ate","nat","bat"]))
console.log(groupAnagrams(["",""]))
