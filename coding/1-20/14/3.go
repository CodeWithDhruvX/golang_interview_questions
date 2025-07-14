package main

import (
	"fmt"
)

// Variadic function to calculate average of float64 values
func average(nums ...float64) float64 {
	if len(nums) == 0 {
		return 0.0
	}
	total := 0.0
	for _, num := range nums {
		total += num
	}
	return total / float64(len(nums))
}

func main() {
	fmt.Println("Average 1:", average(10.5, 20.0, 30.5))
	fmt.Println("Average 2:", average())
}
