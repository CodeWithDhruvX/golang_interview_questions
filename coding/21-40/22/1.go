package main

import "fmt"

func main() {
	fruits := []string{"apple", "banana"}

	// Append a single element
	fruits = append(fruits, "cherry")

	// Append multiple elements
	append(fruits, "date", "elderberry")

	fmt.Println("Updated slice:", fruits)
}
