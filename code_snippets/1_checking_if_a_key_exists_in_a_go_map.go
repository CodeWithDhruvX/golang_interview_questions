// 90% of Go beginners mess this up when checking if a key exists in a map!
// Checking if a Key Exists in a Go Map

// Go
// Problem:
package main
import "fmt"
func main() {
	m := map[string]int{"a": 1}
	val := m["b"] // direct access
	fmt.Println(val) // Output: 0, but does key exist?
}

// Solution:
package main
import "fmt"
func main() {
	m := map[string]int{"a": 1}
	val, ok := m["b"] // check existence
	fmt.Println("Value:", val, "Exists?", ok) // Output: Value: 0 Exists? false
}