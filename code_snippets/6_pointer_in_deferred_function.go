// Deferred functions capture pointers—use this to get updated values!
// Pointer in Deferred Function

// Go
// Problem:
var x int = 5
defer fmt.Println(&x)
x = 10 // prints pointer to x

// Solution:
package main
import "fmt"
func main() {
    x := 5
    defer func(p *int) { fmt.Println(*p) }(&x)
    x = 10
}
// Output: 10