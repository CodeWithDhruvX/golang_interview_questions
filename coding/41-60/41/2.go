package main

import "fmt"

func increment(num *int) {
	*num = *num + 1
}

func main() {
	x := 5
	fmt.Println("Before increment:", x)

	increment(&x)

	fmt.Println("After increment:", x)
}
