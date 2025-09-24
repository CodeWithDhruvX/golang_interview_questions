// Looping over slices of structs? Avoid this common pointer mistake!
// Pointer with Struct Slice

// Go
// Problem:
s := []Point{{1,2},{3,4}}
for _, p := range s { p.X++ }
fmt.Println(s[0].X) // 1 ❌ not updated

// Solution:
package main
import "fmt"
type Point struct { X,Y int }
func main() {
    s := []Point{{1,2},{3,4}}
    for i := range s {
        ptr := &s[i]
        ptr.X++
    }
    fmt.Println(s[0].X)
}
// Output: 2