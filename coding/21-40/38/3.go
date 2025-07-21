package main

import (
	"encoding/json"
	"fmt"
)

type Person struct {
	Name string
	Age  int
}

func isEqualByJSON(a, b Person) bool {
	aj, _ := json.Marshal(a)
	bj, _ := json.Marshal(b)
	return string(aj) == string(bj)
}

func main() {
	p1 := Person{Name: "Charlie", Age: 40}
	p2 := Person{Name: "Charlie", Age: 40}

	fmt.Println("Equal by JSON:", isEqualByJSON(p1, p2))
}
