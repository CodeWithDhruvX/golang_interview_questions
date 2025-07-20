package main

import "fmt"

// Creating a type alias
type Kilometers = int

func addDistance(a, b Kilometers) Kilometers {
	return a + b
}

func main() {
	var distance1 Kilometers = 5
	var distance2 Kilometers = 10
	total := addDistance(distance1, distance2)

	fmt.Printf("Total distance: %d km\n", total)
}
