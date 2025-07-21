package main

import "fmt"

func extendSlice(s *[]int) {
	*s = append(*s, 4, 5)
}

func main() {
	numbers := []int{1, 2, 3}
	extendSlice(&numbers)
	fmt.Println("Modified slice:", numbers)
}
