package main

import (
	"fmt"
	"reflect"
)

type Person struct {
	Name string
	Age  int
}

func main() {
	a := Person{Name: "Alice", Age: 30}
	b := Person{Name: "Alice", Age: 30}

	equal := reflect.DeepEqual(a, b)
	fmt.Println("Are a and b equal?", equal)
}
