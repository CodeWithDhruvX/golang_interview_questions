package main

import (
	"fmt"
)

type Person struct {
	Name    string
	Friends []string
}

func main() {
	original := Person{
		Name:    "Alice",
		Friends: []string{"Bob", "Charlie"},
	}

	// Shallow copy
	copy := original
	copy.Friends[0] = "David"

	fmt.Println("Original:", original.Friends)
	fmt.Println("Copy    :", copy.Friends)
}
