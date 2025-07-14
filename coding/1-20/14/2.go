package main

import (
	"fmt"
	"strings"
)

// Variadic function to join strings
func joinStrings(sep string, words ...string) string {
	return strings.Join(words, sep)
}

func main() {
	result := joinStrings("-", "go", "is", "fun")
	fmt.Println("Joined:", result)
}
