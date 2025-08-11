package main

import "fmt"

func main() {
	// Normal append
	nums := []int{1, 2, 3}
	nums = append(nums, 4)
	fmt.Println(nums) // [1 2 3 4]

	// Remove element without loop (remove index
	// 2 → value 3)
	nums2 := []int{1, 2, 3, 4, 5}
	nums2 = append(nums2[:2], nums2[3:]...)
	fmt.Println(nums2) // [1 2 4 5]
}
