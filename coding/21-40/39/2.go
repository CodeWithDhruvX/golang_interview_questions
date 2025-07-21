package main

import "fmt"

type Person struct {
	Name    string
	Friends []string
}

func deepCopy(p Person) Person {
	newFriends := make([]string, len(p.Friends))
	copy(newFriends, p.Friends)
	return Person{
		Name:    p.Name,
		Friends: newFriends,
	}
}

func main() {
	original := Person{"Alice", []string{"Bob", "Charlie"}}
	copy := deepCopy(original)

	copy.Friends[0] = "David"

	fmt.Println("Original:", original.Friends)
	fmt.Println("Copy    :", copy.Friends)
}
