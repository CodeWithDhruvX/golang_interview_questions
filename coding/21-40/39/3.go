package main

import (
	"encoding/json"
	"fmt"
)

type Person struct {
	Name    string
	Friends []string
}

func deepCopyJSON(p Person) Person {
	var copy Person
	data, _ := json.Marshal(p)
	_ = json.Unmarshal(data, &copy)
	return copy
}

func main() {
	original := Person{"Alice", []string{"Bob", "Charlie"}}
	copy := deepCopyJSON(original)

	copy.Friends[0] = "David"

	fmt.Println("Original:", original.Friends)
	fmt.Println("Copy    :", copy.Friends)
}
