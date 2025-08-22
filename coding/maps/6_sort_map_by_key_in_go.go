// Go maps are unordered—but here’s how to sort them by key!
// Sort Map by Key in Go

// Go
package main
import (
    "fmt"
    "slices"
)

func main() {
    m := map[string]int{"b": 2, "a": 1}
    keys := []string{}
    for k := range m {
        keys = append(keys, k)
    }
    slices.Sort(keys)
    for _, k := range keys {
        fmt.Println(k, m[k])
    }
    // Output: a 1 \n b 2
}