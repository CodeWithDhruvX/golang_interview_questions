package main

import "fmt"

func main() {
	// Array occupies exact space for 5 elements
	arr := [5]string{"a", "b", "c", "d", "e"}

	// Slice from index 1 to 3 (excluding 4)
	slice := arr[1:4]
	fmt.Println("Original Array:", arr)
	fmt.Println("Slice:", slice)
	fmt.Printf("Slice len: %d, cap: %d\n",
		len(slice), cap(slice))

	// Append to slice
	slice = append(slice, "z")
	fmt.Println("After Append:", slice)
}
