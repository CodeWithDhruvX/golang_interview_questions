package main

import "fmt"

func increment(n *int) {
	*n = *n + 1
}

func main() {
	val := 5
	fmt.Println("Before increment:", val)

	increment(&val)
	fmt.Println("After increment:", val)
}
