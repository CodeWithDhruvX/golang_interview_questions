package main

import (
	"fmt"
)

func main() {
	m := map[string]int{"apple": 5, "banana": 10}

	if val, exists := m["banana"]; exists {
		fmt.Printf("Found 'banana' with value: %d\n", val)
	} else {
		fmt.Println("'banana' key not found")
	}
}
