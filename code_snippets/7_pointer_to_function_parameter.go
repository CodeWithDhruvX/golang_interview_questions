// Function parameters in Go don’t update without pointers—here’s the fix!
// Pointer to Function Parameter

// Go
// Problem:
// func double(n int) { n *= 2 }
// x := 5
// double(x)
// fmt.Println(x) // 5 ❌ unchanged

// Solution:
package main

import "fmt"

func double(n *int) { *n *= 2 }
func main() {
	x := 5
	double(&x)
	fmt.Println(x)
}

// Output: 10
