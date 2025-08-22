// Save memory in Go by reordering struct fields!
// Memory optimization with structs

// Go
package main
import (
    "fmt"
    "unsafe"
)
type Bad struct {
    A byte
    B int64
    C byte
}
type Good struct {
    B int64
    A byte
    C byte
}
func main() {
    fmt.Println(unsafe.Sizeof(Bad{}))  // Output: 24
    fmt.Println(unsafe.Sizeof(Good{})) // Output: 16
}