package main

import "fmt"

func riskyOperation() (result int) {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Recovered from panic:", r)
			result = -1
		}
	}()
	result = 100
	panic("Something went wrong!")
}

func main() {
	fmt.Println("Final Result:", riskyOperation())
}
