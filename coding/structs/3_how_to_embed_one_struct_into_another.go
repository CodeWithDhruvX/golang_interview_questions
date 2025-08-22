// Inheritance doesn’t exist in Go — but embedding does!
// How to embed one struct into another?

// Go
package main
import "fmt"
type Person struct {
    Name string
}
type Employee struct {
    Person // embedded
    ID int
}
func main() {
    e := Employee{Person{"Carol"}, 101}
    fmt.Println(e.Name, e.ID)
}
// Output: Carol 101