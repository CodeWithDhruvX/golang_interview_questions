package main

import "fmt"

func main() {
	// Array with fixed size
	var arr = [3]int{1, 2, 3}
	fmt.Println("Array:", arr)

	// Slice derived from array
	slice := arr[:]
	fmt.Println("Slice:", slice)

	// Modify array and see impact on slice
	arr[0] = 100
	fmt.Println("Modified Array:", arr)
	fmt.Println("Slice reflects change:", slice)
}
