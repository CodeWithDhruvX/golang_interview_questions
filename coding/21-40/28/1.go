package main

import "fmt"

func modifySlice(s []int) {
	s[0] = 99
	fmt.Println("Inside function:", s)
}

func main() {
	numbers := []int{1, 2, 3}
	modifySlice(numbers)
	fmt.Println("Outside function:", numbers)
}
