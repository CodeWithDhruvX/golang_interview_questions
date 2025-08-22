// Think assigning copies a Go map? Wrong—here’s the right way!
// Copy Map in Go

// Go
package main
import "fmt"

func main() {
    m1 := map[string]int{"a": 1}
    m2 := map[string]int{}
    for k, v := range m1 {
        m2[k] = v
    }
    fmt.Println(m1, m2)
    // Output: map[a:1] map[a:1]
}