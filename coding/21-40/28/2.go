package main

import "fmt"

func appendToSlice(s []int) {
	s = append(s, 100)
	fmt.Println("Inside function:", s)
}

func main() {
	numbers := []int{1, 2, 3}
	appendToSlice(numbers)
	fmt.Println("Outside function:", numbers)
}
