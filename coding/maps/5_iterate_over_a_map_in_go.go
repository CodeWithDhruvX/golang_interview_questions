// Want to loop through a map in Go? Here’s the gotcha!
// Iterate Over a Map in Go

// Go
package main
import "fmt"

func main() {
    m := map[string]int{"a": 1, "b": 2}
    for k, v := range m {
        fmt.Println(k, v)
    }
    // Output: order is random
}