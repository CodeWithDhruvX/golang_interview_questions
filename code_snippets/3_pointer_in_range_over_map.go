// Looping over maps? Here’s why pointers inside range fail!
// Pointer in Range Over Map

// Go
// Problem:
m := map[string]int{"a":1,"b":2}
for k, v := range m {
    ptr := &v
    *ptr *= 2
}
fmt.Println(m) // unchanged ❌

// Solution:
package main
import "fmt"
func main() {
    m := map[string]int{"a":1,"b":2}
    for k := range m {
        m[k] *= 2
    }
    fmt.Println(m)
}
// Output: map[a:2 b:4]