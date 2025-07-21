package main

import (
	"encoding/json"
	"fmt"
)

type Address struct {
	City string
	Zip  string
}

type Employee struct {
	ID      int
	Name    string
	Address Address
}

func main() {
	emp := Employee{
		ID:   101,
		Name: "John Doe",
		Address: Address{
			City: "New York",
			Zip:  "10001",
		},
	}

	result, _ := json.MarshalIndent(emp, "", "  ")
	fmt.Println(string(result))
}
