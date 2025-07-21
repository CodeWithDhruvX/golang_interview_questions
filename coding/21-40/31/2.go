package main

import (
	"fmt"
)

func main() {
	data := map[int]string{
		1: "One",
		2: "Two",
	}

	keyToDelete := 3

	// Check if key exists before delete
	if _, exists := data[keyToDelete]; exists {
		fmt.Printf("Deleting key: %d\n", keyToDelete)
		delete(data, keyToDelete)
	} else {
		fmt.Printf("Key %d does not exist. Safe to skip delete.\n", keyToDelete)
	}

	fmt.Println("Final map state:", data)
}
