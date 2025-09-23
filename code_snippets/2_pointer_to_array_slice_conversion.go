// Pointers to arrays can be sliced—boost your in-place edits!
// Pointer to Array Slice Conversion

// Go
// Problem:
arr := [3]int{1,2,3}
var ptr *[3]int = &arr
slice := ptr[:] // works ✅

// Solution:
package main
import "fmt"
func main() {
    arr := [3]int{1,2,3}
    ptr := &arr
    slice := ptr[:]
    for i := range slice {
        slice[i] *= 2
    }
    fmt.Println(arr)
}
// Output: [2 4 6]