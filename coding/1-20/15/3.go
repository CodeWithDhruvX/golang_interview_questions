package main

import "fmt"

// Alias (same underlying type)
type AgeAlias = int

// New type (not interchangeable)
type AgeNew int

func main() {
	var original int = 25

	var alias AgeAlias = original         // ✅ Works
	var newType AgeNew = AgeNew(original) // ✅ Needs conversion

	fmt.Println("Alias age:", alias)
	fmt.Println("New type age:", newType)
}
