package main

import "fmt"

func main() {
	var nums []int

	for i := 0; i < 10; i++ {
		nums = append(nums, i)
		fmt.Printf("After appending %d -> len: %d, cap: %d\n", i, len(nums), cap(nums))
	}
}
