// You can even use pointers to channels—here’s how!
// Pointer to Channel

// Go
// Problem:
ch := make(chan int)
ptr := &ch // trying to pass pointer to send?

// Solution:
package main
import "fmt"
func send(ch *chan int, val int) {
    *ch <- val // send via pointer
}
func main() {
    ch := make(chan int)
    go func() {
        send(&ch, 42)
    }()
    fmt.Println(<-ch)
}
// Output: 42


give two seperate code snippet in a single file with the problem and solution statement