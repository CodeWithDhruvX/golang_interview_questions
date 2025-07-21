package main

import (
	"fmt"
)

func main() {
	rows, cols := 3, 4
	matrix := make([][]int, rows)

	for i := range matrix {
		matrix[i] = make([]int, cols)
		for j := range matrix[i] {
			matrix[i][j] = i*cols + j
		}
	}

	fmt.Println("2D Matrix:")
	for _, row := range matrix {
		fmt.Println(row)
	}
}
