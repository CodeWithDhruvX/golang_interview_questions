package main

import "fmt"

func add(a, b int) (sum int) {
	sum = a + b
	return
}

func main() {
	result := add(10, 15)
	fmt.Println("Sum is:", result)
}
