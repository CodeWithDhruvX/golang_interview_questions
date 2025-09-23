// Need to manipulate deeply nested structs? Pointers make it simple!
// Pointer in Nested Struct

// Go
// Problem:
type Inner struct { Val int }
type Outer struct { I Inner }
o := Outer{Inner{5}}
ptr := &o.I.Val
*ptr++
fmt.Println(o.I.Val) // 6 ✅ okay

// Solution:
package main
import "fmt"
type Inner struct { Val int }
type Outer struct { I Inner }
func main() {
    o := Outer{Inner{5}}
    ptr := &o.I.Val
    *ptr++
    fmt.Println(o.I.Val)
}
// Output: 6