package main

import "fmt"

func main() {
	base := []int{1, 2, 3}
	extra := []int{4, 5, 6}

	// Use spread operator to append all elements from extra
	base = append(base, extra...)

	fmt.Println("Combined slice:", base)
}
