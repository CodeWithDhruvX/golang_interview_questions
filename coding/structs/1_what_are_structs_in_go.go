// Classes don’t exist in Go — so how do you group data?
// What are structs in Go?

// Go
package main
import "fmt"
type Person struct {
    Name string
    Age  int
}
func main() {
    p := Person{"Alice", 30}
    fmt.Println(p)
}
// Output: {Alice 30}