package main

import "fmt"

type Person struct {
	Name string
	Age  int
}

func areEqual(p1, p2 Person) bool {
	return p1.Name == p2.Name && p1.Age == p2.Age
}

func main() {
	a := Person{Name: "Bob", Age: 25}
	b := Person{Name: "Bob", Age: 25}

	fmt.Println("Structs equal:", areEqual(a, b))
}
