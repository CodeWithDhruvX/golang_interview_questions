// What if I told you Go auto-dereferences pointers?
// Go Pointer Deref Shortcut

// Go
package main
import "fmt"

type Point struct { x int }

func main() {
    p := &Point{5}
    fmt.Println(p.x)   // auto-deref
    (*p).x = 10
    fmt.Println(p.x)
    // Output:
    // 5
    // 10
}