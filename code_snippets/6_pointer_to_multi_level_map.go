// Want to modify nested maps directly? Pointers make it simple!
// Pointer to Multi-level Map

// Go
// Problem:
m := map[string]map[string]int{"a":{"x":1}}
val := m["a"]["x"]
val++
fmt.Println(m["a"]["x"]) // 1 ❌ not updated

// Solution:
package main
import "fmt"
func main() {
    m := map[string]map[string]int{"a":{"x":1}}
    ptr := &m["a"]["x"]
    *ptr++
    fmt.Println(m["a"]["x"])
}
// Output: 2