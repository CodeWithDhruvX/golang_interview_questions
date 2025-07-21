package main

import "fmt"

func main() {
	// Declare a slice using shorthand
	numbers := []int{10, 20}
	fmt.Println("Initial Slice:", numbers)

	// Append new elements dynamically
	numbers = append(numbers, 30, 40)
	fmt.Println("After Append:", numbers)

	// Slices grow dynamically; arrays cannot
}
