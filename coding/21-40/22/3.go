package main

import "fmt"

func main() {
	var numbers []int

	for i := 1; i <= 5; i++ {
		numbers = append(numbers, i*i) // appending squares
	}

	fmt.Println("Dynamic slice:", numbers)
}
