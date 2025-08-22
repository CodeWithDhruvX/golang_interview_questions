// Here’s a subtle memory trap with maps in Go!
// Map Memory Pitfall in Go

// Go
package main
import "fmt"

func main() {
    m := map[int]*int{}
    x := 42
    m[1] = &x
    delete(m, 1)
    fmt.Println(m)
    // Output: map[] (value GC after delete)
}