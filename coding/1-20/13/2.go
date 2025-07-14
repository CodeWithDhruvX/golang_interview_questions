package main

import "fmt"

func calculate() (result int) {
	defer func() {
		result += 5
	}()
	result = 10
	return
}

func main() {
	fmt.Println("Final Result:", calculate())
}
