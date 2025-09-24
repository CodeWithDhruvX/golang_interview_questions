// Update struct inside slice correctly using pointers!
// Pointer to Slice Element Struct

// Go
// Problem:
type Point struct { X int }
pts := []Point{{1},{2}}
p := pts[0]
p.X++
fmt.Println(pts[0].X) // 1 ❌ unchanged

// Solution:
package main
import "fmt"
type Point struct { X int }
func main() {
    pts := []Point{{1},{2}}
    ptr := &pts[0]
    ptr.X++
    fmt.Println(pts[0].X)
}
// Output: 2