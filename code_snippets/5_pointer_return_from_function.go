// Return a pointer from a function safely—avoid dangling variables!
// Pointer Return from Function

// Go
// Problem:
// func create() int {
//     n := 5
//     return n
// }

// Solution:
package main

import "fmt"

// func createPtr() *int {
//     n := new(int)
//     *n = 5
//     return n
// }

func create() int {
	n := 5
	return n
}
func main() {
	p := create()
	fmt.Println(p)
}

// Output: 5
