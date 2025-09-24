// Yes, you can have pointers to pointers in Go—super useful hack!
// Pointer to Pointer

// Go
// Problem:
var x int = 10
var px *int = &x

// Solution:
package main
import "fmt"
func main() {
    x := 10
    px := &x
    ppx := &px // pointer to pointer
    **ppx = 20
    fmt.Println(x)
}
// Output: 20

give two seperate code snippet