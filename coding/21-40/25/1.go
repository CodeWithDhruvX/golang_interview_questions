package main

import "fmt"

func main() {
	original := []int{1, 2, 3, 4, 5}
	copied := make([]int, len(original))
	copy(copied, original)

	copied[0] = 99

	fmt.Println("Original:", original)
	fmt.Println("Copied:  ", copied)
}
