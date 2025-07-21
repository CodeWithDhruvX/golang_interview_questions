package main

import "fmt"

func main() {
	a := 10
	var p *int = &a

	fmt.Println("Value of a:", a)
	fmt.Println("Address of a:", p)
	fmt.Println("Value at pointer p:", *p)

	*p = 20
	fmt.Println("Updated value of a:", a)
}
