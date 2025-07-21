package main

import (
	"fmt"
	"strings"
)

func main() {
	text := "go is fun and go is powerful"
	words := strings.Fields(text)

	freq := make(map[string]int)

	for _, word := range words {
		freq[word]++
	}

	// Print frequency count
	for word, count := range freq {
		fmt.Printf("'%s' appears %d times\n", word, count)
	}
}
