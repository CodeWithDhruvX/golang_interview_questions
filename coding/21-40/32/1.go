package main

import "fmt"

func main() {
	slice1 := []int{1, 2, 3}
	slice2 := []int{4, 5, 6}

	// This will NOT compile: slices are not comparable
	m := map[[]int]string{
		slice1: "first",
		slice2: "second",
	}

	fmt.Println(m)
}
