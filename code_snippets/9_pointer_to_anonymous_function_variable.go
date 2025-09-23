// Use pointers inside closures for real-time value updates!
// Pointer to Anonymous Function Variable

// Go
// Problem:
x := 5
f := func() int { return x }
x = 10
fmt.Println(f()) // 10 ✅ but pointer idea?

// Solution:
package main
import "fmt"
func main() {
    x := 5
    px := &x
    f := func() int { return *px }
    *px = 10
    fmt.Println(f())
}
// Output: 10