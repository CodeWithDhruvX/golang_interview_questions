package main

import "fmt"

func main() {
	nums := make([]int, 3, 5) // length 3, capacity 5

	fmt.Println("Slice:", nums)
	fmt.Println("Length:", len(nums))   // Actual number of elements
	fmt.Println("Capacity:", cap(nums)) // Total storage allocated

	nums = append(nums, 10, 20)
	fmt.Println("After append:", nums)
	fmt.Println("Length now:", len(nums))
	fmt.Println("Capacity now:", cap(nums))
}
