package main

import (
	"fmt"
)

func main() {
	ages := map[string]int{
		"Alice": 25,
		"Bob":   30,
		"Eve":   28,
	}

	// Add a new entry
	ages["Charlie"] = 35

	// Update an existing entry
	ages["Alice"] = 26

	// Delete a key
	delete(ages, "Eve")

	// Check existence
	if age, exists := ages["Bob"]; exists {
		fmt.Printf("Bob's age is %d\n", age)
	}

	// Iterate over the map
	for name, age := range ages {
		fmt.Printf("%s is %d years old.\n", name, age)
	}
}
