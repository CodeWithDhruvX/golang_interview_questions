// You can’t point to constants—here’s the right way!
// Pointer to Const Value

// Go
// Problem:
const x = 10
ptr := &x // ❌ illegal

// Solution:
package main
import "fmt"
func main() {
    x := 10 // mutable variable
    ptr := &x
    *ptr++
    fmt.Println(x)
}
// Output: 11