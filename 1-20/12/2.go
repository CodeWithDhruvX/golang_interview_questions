package main

import "fmt"

func computeValue() int {
	var result int
	defer func(val *int) {
		*val += 10
	}(&result)
	result = 20
	return result
}

func main() {
	fmt.Println("Returned Value:", computeValue())
}
