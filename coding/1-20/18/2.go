package main

import "fmt"

func main() {
	names := []string{"Rahul", "Amit", "Sneha"}

	for _, name := range names {
		fmt.Println("Hello", name)
	}
}
