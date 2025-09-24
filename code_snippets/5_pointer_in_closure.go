// Closures and pointers can silently break your loops—fix it fast!
// Pointer in Closure

// Go
// Problem:
func makeIncrementers() []func() int {
    var funcs []func() int
    for i := 0; i < 3; i++ {
        funcs = append(funcs, func() int { return i })
    }
    return funcs
}
// Issue: all funcs return 3 ❌

// Solution:
package main
import "fmt"
func makeIncrementers() []func() int {
    var funcs []func() int
    for i := 0; i < 3; i++ {
        j := i // pointer capture trick
        funcs = append(funcs, func() int { return j })
    }
    return funcs
}
func main() {
    incs := makeIncrementers()
    for _, f := range incs {
        fmt.Println(f())
    }
}
// Output: 0 1 2