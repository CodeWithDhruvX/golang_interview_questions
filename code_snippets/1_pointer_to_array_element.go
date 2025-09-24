// Want to update array elements efficiently? Pointers to the rescue!
// Pointer to Array Element

// Go
// Problem:
arr := [3]int{1,2,3}
ptr := &arr[0]
*ptr = 10
fmt.Println(arr) // 10 ✅ only first element

// Solution:
package main
import "fmt"
func main() {
    arr := [3]int{1,2,3}
    for i := range arr {
        ptr := &arr[i] // pointer each
        *ptr *= 2
    }
    fmt.Println(arr)
}
// Output: [2 4 6]