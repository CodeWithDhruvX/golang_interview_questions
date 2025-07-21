package main

import "fmt"

type Address struct {
	City  string
	State string
}

type Company struct {
	Name    string
	Address Address
}

func main() {
	comp := Company{
		Name: "TechCorp",
		Address: Address{
			City:  "San Francisco",
			State: "CA",
		},
	}

	fmt.Printf("%s is located in %s, %s\n", comp.Name, comp.Address.City, comp.Address.State)
}
