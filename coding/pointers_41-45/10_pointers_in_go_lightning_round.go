// I’ll teach you Go pointers in 30 seconds flat!
// Pointers in Go Lightning Round

// Go
package main
import "fmt"

func main() {
    var p *int
    i := 7
    p = &i
    fmt.Println(*p)   // deref
    if p != nil { fmt.Println("Pointer is not nil") }
    // Output:
    // 7
    // Pointer is not nil
}