// Nil or empty slices can panic with pointers—avoid it like this!
// Pointer with Nil Slice

// Go
// Problem:
var s []int
ptr := &s[0] // ❌ panic

// Solution:
package main
import "fmt"
func main() {
    s := []int{1,2,3}
    ptr := &s[0]
    fmt.Println(*ptr)
}
// Output: 1