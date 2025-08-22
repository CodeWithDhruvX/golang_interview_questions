// This Go mistake will cost you hours of debugging!
// The Silent Bug in Go Methods

// Go
package main
import "fmt"

type Counter struct { n int }

func (c Counter) IncValue() { c.n++ }      // copy
func (c *Counter) IncPointer() { c.n++ }   // real

func main() {
    c := Counter{0}
    c.IncValue()
    fmt.Println(c.n) // 0 (bug!)
    c.IncPointer()
    fmt.Println(c.n) // 1
    // Output:
    // 0
    // 1
}