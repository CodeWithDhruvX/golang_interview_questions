// Think Go pointers work like C? Think again…
// Go Pointers vs C Pointers

// Go
package main
import "fmt"

func main() {
    x := 10
    p := &x
    fmt.Println(*p)
    // No pointer arithmetic in Go
    // Output: 10
}