// Think you can compare two maps in Go? Nope—this is a trick question.
// Can Maps Be Compared in Go?

// Go
// Problem:
// package main
// func main() {
// 	m1 := map[string]int{"a":1}
// 	m2 := map[string]int{"a":1}
// 	// fmt.Println(m1 == m2) // compile error
// }

// Solution:
package main

import (
	"fmt"
	"reflect"
)

func main() {
	m1 := map[string]int{"a": 1}
	m2 := map[string]int{"a": 1}
	fmt.Println("Nil compare:", m1 == nil)               // Output: false
	fmt.Println("DeepEqual:", reflect.DeepEqual(m1, m2)) // Output: true
}
