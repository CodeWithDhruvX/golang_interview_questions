// Slices share arrays—avoid surprises with a simple copy trick!
// Pointer Array vs Slice

// Go
// Problem:
arr := [3]int{1,2,3}
slice := arr[:]
slice[0] = 99
fmt.Println(arr) // 99 ✅ slice shares array

// Solution:
package main
import "fmt"
func main() {
    arr := [3]int{1,2,3}
    slice := make([]int, len(arr))
    copy(slice, arr) // independent
    slice[0] = 99
    fmt.Println(arr)
}
// Output: [1 2 3]