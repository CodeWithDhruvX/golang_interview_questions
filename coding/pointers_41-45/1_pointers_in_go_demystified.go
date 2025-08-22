// If you can’t explain pointers in Go, you’ll fail your interview…
// Pointers in Go Demystified

// Go
package main
import "fmt"

func main() {
    x := 42
    p := &x           // pointer to x
    fmt.Println(*p)   // dereference
    *p = 100          // update value
    fmt.Println(x)    // x updated
    // Output:
    // 42
    // 100
}