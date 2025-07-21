package main

import "fmt"

func main() {
	// Initialize empty map
	colors := make(map[string]string)

	// Try to delete a key from empty map
	delete(colors, "red")

	// Still safe, no panic or error
	fmt.Println("No panic. Current map:", colors)
}
