// Did you know you can create structs without a name?
// Anonymous structs in Go

// Go
package main
import "fmt"
func main() {
    user := struct {
        Name string
        Age  int
    }{"Eve", 28}
    fmt.Println(user)
}
// Output: {Eve 28}