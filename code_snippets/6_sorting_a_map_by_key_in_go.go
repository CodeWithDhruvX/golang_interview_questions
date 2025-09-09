// Go maps are unordered—so how do you sort them?
// Sorting a Map by Key in Go

// Go
// Problem:
package main
import "fmt"
func main() {
	m := map[string]int{"b":2,"a":1}
	// range preserves order? no
}

// Solution:
package main
import (
	"fmt"
	"sort"
)
func main() {
	m := map[string]int{"b":2,"a":1}
	keys := make([]string, 0, len(m))
	for k := range m { keys = append(keys, k) }
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Println(k, m[k]) // Output: a 1 \n b 2
	}
}