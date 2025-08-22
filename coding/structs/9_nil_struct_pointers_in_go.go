// Accessing a nil struct pointer? That’s a runtime panic!
// Nil struct pointers in Go

// Go
package main
import "fmt"
type Person struct {
    Name string
}
func main() {
    var p *Person // nil pointer
    if p == nil {
        fmt.Println("Safe: struct is nil")
    }
}
// Output: Safe: struct is nil