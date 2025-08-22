// Yes, structs can be compared — but only if all fields are comparable!
// How do you compare two structs?

// Go
package main
import "fmt"
type Point struct {
    X int
    Y int
}
func main() {
    p1 := Point{1, 2}
    p2 := Point{1, 2}
    fmt.Println(p1 == p2)
}
// Output: true