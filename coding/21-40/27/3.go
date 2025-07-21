package main

import (
	"fmt"
)

type Row struct {
	Values []int
}

func main() {
	rows := 3
	matrix := make([]Row, rows)

	for i := range matrix {
		matrix[i] = Row{Values: make([]int, 4)}
		for j := range matrix[i].Values {
			matrix[i].Values[j] = i*10 + j
		}
	}

	fmt.Println("Struct-based Matrix:")
	for _, row := range matrix {
		fmt.Println(row.Values)
	}
}
