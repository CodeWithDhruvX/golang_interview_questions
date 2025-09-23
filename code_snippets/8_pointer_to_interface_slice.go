// Pointers to slice elements prevent copying surprises!
// Pointer to Interface Slice

// Go
// Problem:
arr := []interface{}{1,2,3}
for _, v := range arr { pv := &v; fmt.Println(*pv) }
// prints copies ❌

// Solution:
package main
import "fmt"
func main() {
    arr := []interface{}{1,2,3}
    for i := range arr {
        pv := &arr[i]
        fmt.Println(*pv)
    }
}
// Output: 1 2 3