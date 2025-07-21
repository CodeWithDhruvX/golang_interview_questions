package main

import "fmt"

func expand(s []int) []int {
	s = append(s, 100)
	s[0] = 42
	return s
}

func main() {
	nums := []int{1, 2}
	expanded := expand(nums)

	fmt.Println("Original:", nums)
	fmt.Println("Expanded:", expanded)
}
