package main

import (
	"fmt"
)

func main() {
	slice := make([]int, 0, 2)
	for i := 1; i <= 5; i++ {
		slice = append(slice, i)
		fmt.Printf("After append %d => len: %d cap: %d addr: %p\n", i, len(slice), cap(slice), &slice[0])
	}
}
