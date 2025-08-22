// Passing big structs by value? RIP performance!
// The #1 Pointer Mistake in Go

// Go
package main
import "fmt"

type Big struct { data [1000]int }

func changeValue(b Big) { b.data[0] = 1 }       // copy
func changePointer(b *Big) { b.data[0] = 1 }   // efficient

func main() {
    var b Big
    changeValue(b)
    fmt.Println(b.data[0]) // 0
    changePointer(&b)
    fmt.Println(b.data[0]) // 1
    // Output:
    // 0
    // 1
}