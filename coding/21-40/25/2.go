package main

import "fmt"

func main() {
	original := []int{10, 20, 30, 40}
	copied := append([]int(nil), original...)

	copied[1] = 99

	fmt.Println("Original:", original)
	fmt.Println("Copied:  ", copied)
}
