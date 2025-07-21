package main

import "fmt"

func main() {
	original := []int{100, 200, 300}
	copied := make([]int, 0, len(original))

	for _, val := range original {
		copied = append(copied, val)
	}

	copied[2] = 999

	fmt.Println("Original:", original)
	fmt.Println("Copied:  ", copied)
}
