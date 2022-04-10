package main

import "fmt"

func HasPairWithSum(arr []int, sum int) bool {
	comp := make(map[int]struct{})
	for _, v := range arr {
		if _, found := comp[v]; found {
			return true
		}
		comp[sum-v] = struct{}{}
	}
	return false
}

func main() {
	input1 := []int{1, 2, 4, 9}
	fmt.Println(HasPairWithSum(input1, 8))

	input2 := []int{1, 9, 3, 6, 1, 7, 9}
	fmt.Println(HasPairWithSum(input2, 8))
}
