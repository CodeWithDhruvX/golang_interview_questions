// 90% of Go beginners check map keys wrong—here’s the safe way!
// Check if Key Exists in Go Map

// Go
package main
import "fmt"

func main() {
    m := map[string]int{"a": 1}
    v, ok := m["b"] // check key
    fmt.Println(v, ok)
    // Output: 0 false
}