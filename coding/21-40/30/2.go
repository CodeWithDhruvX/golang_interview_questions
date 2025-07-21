package main

import (
	"fmt"
)

func keyExists(m map[string]int, key string) bool {
	_, exists := m[key]
	return exists
}

func main() {
	data := map[string]int{"dog": 1, "cat": 2}

	if keyExists(data, "dog") {
		fmt.Println("'dog' key exists!")
	} else {
		fmt.Println("'dog' key does not exist.")
	}
}
