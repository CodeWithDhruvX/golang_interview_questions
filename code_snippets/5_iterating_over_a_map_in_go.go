// Want to loop through a Go map? Here’s the right way.
// Iterating Over a Map in Go

// Go
// Problem:
package main
import "fmt"
func main() {
	m := map[string]int{"a":1,"b":2}
	// for expecting order
}

// Solution:
package main
import "fmt"
func main() {
	m := map[string]int{"a":1,"b":2}
	for k, v := range m {
		fmt.Println(k, v) // Output: order random
	}
}