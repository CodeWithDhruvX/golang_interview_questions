// Pointers can be safely used inside select statements—here’s the trick!
// Pointer in Select Statement

// Go
// Problem:
ch1 := make(chan int)
ch2 := make(chan int)
// trying to use pointer inside select incorrectly

// Solution:
package main
import "fmt"
func main() {
    ch1 := make(chan int)
    ch2 := make(chan int)
    go func() { ch1 <- 5 }()
    select {
    case val := <-ch1:
        fmt.Println(&val)
    case ch := <-(&ch2): // pointer channel receive
        fmt.Println(ch)
    }
}
// Output: pointer address