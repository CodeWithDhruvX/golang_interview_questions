package main

import "fmt"

func main() {
	defer func() {
		if r := recover(); r != nil {
			fmt.Println("Recovered from panic:", r)
		}
	}()

	fmt.Println("Before panic")
	panic("Something went wrong!") // Simulating a crash
	fmt.Println("This will not print")
}
