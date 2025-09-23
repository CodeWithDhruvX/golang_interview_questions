// Pointer comparisons can be tricky—learn what actually matches!
// Pointer Comparison Gotcha

// Go
// Problem:
// a := 5
// b := 5
// fmt.Println(&a == &b) // false ❌ different addresses

// Solution:
package main

import "fmt"

func main() {

	a := 5
	b := a
	fmt.Println(&a == &b)
	pa := &a
	pb := &a
	fmt.Println(pa == pb) // true
}

// Output: true
