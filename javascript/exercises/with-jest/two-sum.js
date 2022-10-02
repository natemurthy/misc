function twoSum(num, target) {
  for (let i=0; i < num.length-1; i++) {
    for (let j=1; j < num.length; j++) {
      if (num[i]+num[j] == target) {
        return [i,j];   
      }
    }
  }
}

module.exports = twoSum;
