package main

import (
	"fmt"
	"strconv"
)

func main() {
	value := "42"

	// Only interested in the integer result, not the error
	num, _ := strconv.Atoi(value)

	fmt.Println("Converted number:", num)
}
