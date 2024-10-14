// https://leetcode.com/problems/group-anagrams/submissions/946255506/
function groupAnagrams(strs) {
    var anagramMap = new Map();
    for (var _i = 0, strs_1 = strs; _i < strs_1.length; _i++) {
        var s = strs_1[_i];
        var sortedStr = s.split('').sort().join('');
        var maybeValue = anagramMap.get(sortedStr);
        if (maybeValue == undefined) {
            anagramMap.set(sortedStr, [s]);
        }
        else {
            anagramMap.set(sortedStr, maybeValue.concat([s]));
        }
    }
    return Array.from(anagramMap.values());
}
console.log(groupAnagrams(["eat", "tea", "tan", "ate", "nat", "bat"]));
console.log(groupAnagrams(["", ""]));
