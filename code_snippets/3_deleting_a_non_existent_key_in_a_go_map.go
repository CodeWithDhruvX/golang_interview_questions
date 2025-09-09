// What happens if you delete a key from a map that doesn’t exist in Go?
// Deleting a Non-Existent Key in a Go Map

// Go
// Problem:
package main
import "fmt"
func main() {
	m := map[string]int{"a":1}
	// delete(m, "b") // What happens?
}

// Solution:
package main
import "fmt"
func main() {
	m := map[string]int{"a":1}
	delete(m, "b") // safe
	fmt.Println(m) // Output: map[a:1]
}