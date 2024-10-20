// https://leetcode.com/problems/product-of-array-except-self/

const N = 10000

function randomArr(n: number): number[] {
        return Array.from({length: n}, () => Math.floor(Math.random() * 9));
}

const bigArr = randomArr(N)

function perf(fn: Function) {
  const start = Date.now();
  fn();
  const end = Date.now();
  const inSeconds = (end - start) / 1000;
  const rounded = Number(inSeconds).toFixed(3);
  console.log(`Runtime: ${rounded}s`)
}

/*
Performance

when N = 100000
Runtime: 14.746s (slow)
Runtime: 0.011s  (fast)

when N = 10000
Runtime: 0.168s  (slow)
Runtime: 0.004s  (fast)
*/

// productExceptSelfSlow runs in O(n^2) time
// https://leetcode.com/problems/product-of-array-except-self/submissions/946259606/
function productExceptSelfSlow(nums: number[]): number[] {
        const n = nums.length
        let result: number[] = []
        for (let i=0; i < n; i++) {
                let p = 1;
                for (let j = 0; j < n; j++) {
                        if (i != j) {
                                p = p*nums[j]
                        }
                }
                result.push(p)
        }
        return result
}

//console.log(productExceptSelfSlow([1,2,3,4]))
//console.log(productExceptSelfSlow([-1,1,0,-3,3]))
perf(() => productExceptSelfSlow(bigArr))


// productExceptSelfFast runs in O(n) time
// https://leetcode.com/problems/product-of-array-except-self/submissions/946273401/
function productExceptSelfFast(nums: number[]): number[] {
        const n = nums.length
        let left = new Array<number>(n)
        left[0] = 1
        for (let l=1; l < left.length; l++) {
               const prev = l-1
               left[l] = nums[prev]*left[prev]
        }

        let right = new Array<number>(n)
        right[right.length-1] = 1
        for (let r=right.length-2; r > -1; r--) {
                const next = r+1
                right[r] = nums[next]*right[next]
        }

        let result = new Array<number>(n)
        for (let i=0; i < result.length; i++) {
                result[i] = left[i]*right[i]
        }
        return result
}

//console.log(productExceptSelfFast([1,2,3,4]))
//console.log(productExceptSelfFast([-1,1,0,-3,3]))
perf(() => productExceptSelfFast(bigArr))
