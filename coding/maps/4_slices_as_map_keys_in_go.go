// Can you use slices as map keys in Go? Watch out for this pitfall!
// Slices as Map Keys in Go

// Go
package main
import "fmt"

func main() {
    // m := map[[]int]string{} // panic: invalid map key type
    arrKey := [2]int{1, 2}
    m := map[[2]int]string{arrKey: "ok"}
    fmt.Println(m)
    // Output: map[[1 2]:ok]
}