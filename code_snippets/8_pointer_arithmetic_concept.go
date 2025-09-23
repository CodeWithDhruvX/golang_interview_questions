// Go doesn’t allow pointer arithmetic—here’s how to loop safely!
// Pointer Arithmetic Concept

// Go
// Problem:
arr := [3]int{1,2,3}
ptr := &arr[0]
ptr++ // ❌ illegal in Go

// Solution:
package main
import "fmt"
func main() {
    arr := [3]int{1,2,3}
    for i := 0; i < len(arr); i++ {
        ptr := &arr[i]
        fmt.Println(*ptr)
    }
}
// Output: 1 2 3