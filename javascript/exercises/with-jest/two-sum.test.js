const twoSum = require('./two-sum');

test('Example 1', () => {
  nums = [2,7,11,15]; target = 9;
  expect(twoSum(nums, target)).toStrictEqual([0,1]);
});

test('Example 2', () => {
  nums = [3,2,4]; target = 6
  expect(twoSum(nums, target)).toStrictEqual([1,2]);
});

test('Example 3', () => {
  nums = [3,3]; target = 6
  expect(twoSum(nums, target)).toStrictEqual([0,1]);
});

test('Example 4', () => {
  nums = [2,3,4,5,6]; target = 7
  expect(twoSum(nums, target)).toStrictEqual([0,3]);
});
