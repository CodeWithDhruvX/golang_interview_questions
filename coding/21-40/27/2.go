package main

import (
	"fmt"
)

func main() {
	var matrix [][]int

	for i := 0; i < 3; i++ {
		row := []int{}
		for j := 0; j < 4; j++ {
			row = append(row, i+j)
		}
		matrix = append(matrix, row)
	}

	fmt.Println("Appended Matrix:")
	for _, row := range matrix {
		fmt.Println(row)
	}
}
