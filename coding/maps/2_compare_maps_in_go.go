// Think you can compare maps with == in Go? Nope—this is a trap!
// Compare Maps in Go

// Go
package main
import (
    "fmt"
    "maps"
)

func main() {
    m1 := map[string]int{"a": 1}
    m2 := map[string]int{"a": 1}
    fmt.Println(maps.Equal(m1, m2))
    // Output: true
}