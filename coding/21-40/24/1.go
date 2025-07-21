package main

import "fmt"

func main() {
	original := make([]int, 2, 2)
	original[0], original[1] = 1, 2

	fmt.Printf("Original: %v | len: %d | cap: %d\n", original, len(original), cap(original))

	extended := append(original, 3)
	extended[0] = 99

	fmt.Printf("Extended: %v | len: %d | cap: %d\n", extended, len(extended), cap(extended))
	fmt.Printf("Original after append: %v\n", original)
}
