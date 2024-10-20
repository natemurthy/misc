// https://leetcode.com/problems/product-of-array-except-self/
// Slow: https://leetcode.com/problems/product-of-array-except-self/submissions/946259606/
// Fast: https://leetcode.com/problems/product-of-array-except-self/submissions/946273401/
function randomArr(n) {
    return Array.from({ length: n }, function () { return Math.floor(Math.random() * 9); });
}
var N = 10000;
var bigArr = randomArr(N);
/*
when N = 100000
Runtime: 14.746s (slow)
Runtime: 0.011s  (fast)

when N = 10000
Runtime: 0.157s  (slow)
Runtime: 0.004s  (fast)
*/
function perf(fn) {
    var start = Date.now();
    fn();
    var end = Date.now();
    var inSeconds = (end - start) / 1000;
    var rounded = Number(inSeconds).toFixed(3);
    console.log("Runtime: ".concat(rounded, "s"));
}
// productExceptSelfSlow runs in O(n^2) time
function productExceptSelfSlow(nums) {
    var n = nums.length;
    console.log("input length", n);
    var result = [];
    for (var i = 0; i < nums.length; i++) {
        var p = 1;
        for (var j = 0; j < nums.length; j++) {
            if (i != j) {
                p = p * nums[j];
            }
        }
        result.push(p);
    }
    return result;
}
//console.log(productExceptSelfSlow([1,2,3,4]))
//console.log(productExceptSelfSlow([-1,1,0,-3,3]))
perf(function () { return productExceptSelfSlow(bigArr); });
// productExceptSelfFast runs in O(n) time
function productExceptSelfFast(nums) {
    var n = nums.length;
    console.log("input length", n);
    var left = new Array(n);
    left[0] = 1;
    for (var l = 1; l < left.length; l++) {
        var prev = l - 1;
        left[l] = nums[prev] * left[prev];
    }
    var right = new Array(n);
    right[right.length - 1] = 1;
    for (var r = right.length - 2; r > -1; r--) {
        var next = r + 1;
        right[r] = nums[next] * right[next];
    }
    var result = new Array(n);
    for (var i = 0; i < result.length; i++) {
        result[i] = left[i] * right[i];
    }
    return result;
}
//console.log(productExceptSelfFast([1,2,3,4]))
//console.log(productExceptSelfFast([-1,1,0,-3,3]))
perf(function () { return productExceptSelfFast(bigArr); });
