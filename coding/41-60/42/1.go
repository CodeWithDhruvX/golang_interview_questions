package main

import "fmt"

func main() {
	var x int = 10
	var p *int = &x // pointer to x

	fmt.Println("Value of x:", x)
	fmt.Println("Address of x:", p)
	fmt.Println("Value at pointer p:", *p)

	*p = 20 // modifying x via pointer
	fmt.Println("Updated value of x:", x)
}
