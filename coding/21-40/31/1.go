package main

import (
	"fmt"
)

func main() {
	// Define a map
	personAge := map[string]int{
		"Alice": 30,
		"Bob":   25,
	}

	// Attempt to delete a key that does not exist
	delete(personAge, "Charlie")

	// Output map to confirm nothing broke
	fmt.Println("Map after deleting non-existent key:", personAge)
}
