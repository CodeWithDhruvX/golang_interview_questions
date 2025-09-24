// Initializing struct pointers properly prevents nasty panics!
// Pointer Field Initialization

// Go
// Problem:
type Node struct { Val int; Next *Node }
var n Node
fmt.Println(n.Next.Val) // panic ❌

// Solution:
package main
import "fmt"
type Node struct { Val int; Next *Node }
func main() {
    n := Node{Val: 1, Next: &Node{Val: 2}}
    fmt.Println(n.Next.Val)
}
// Output: 2

give two seperate code snippet