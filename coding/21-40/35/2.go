package main

import "fmt"

func main() {
	employee := struct {
		ID     int
		Name   string
		Active bool
	}{
		ID:     101,
		Name:   "Bob",
		Active: true,
	}

	fmt.Printf("Employee: %+v\n", employee)
}
