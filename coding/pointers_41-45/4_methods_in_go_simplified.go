// Think Go doesn’t support OOP? Watch this!
// Methods in Go Simplified

// Go
package main
import "fmt"

type Rectangle struct { w, h int }

func (r Rectangle) Area() int { // method
    return r.w * r.h
}

func main() {
    rect := Rectangle{3, 4}
    fmt.Println(rect.Area())
    // Output: 12
}