// Stop wasting time declaring pointers the long way!
// Fast Pointer Declaration in Go

// Go
package main
import "fmt"

func main() {
    p := new(int)     // allocate int pointer
    *p = 99           // assign
    fmt.Println(*p)
    // Output: 99
}