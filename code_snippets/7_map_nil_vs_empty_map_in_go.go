// This Go map question fails 70% of interviewees.
// Map Nil vs Empty Map in Go

// Go
// Problem:
package main
import "fmt"
func main() {
	var m1 map[string]int // nil map
	m2 := map[string]int{} // empty map
	// m1["a"] = 1 // panic
}

// Solution:
package main
import "fmt"
func main() {
	var m1 map[string]int // nil map
	m2 := make(map[string]int) // empty map
	fmt.Println("Nil map:", m1 == nil) // Output: true
	fmt.Println("Empty map:", m2 == nil) // Output: false
	m2["a"] = 1 // safe
	fmt.Println(m2) // Output: map[a:1]
}