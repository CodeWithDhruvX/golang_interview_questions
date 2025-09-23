// Pointers with interfaces can surprise you—here's how to update safely!
// Pointer to Interface Value

// Go
// Problem:
var i interface{} = 5
pi := &i
*pi = 10
fmt.Println(i) // Output might be confusing

// Solution:
package main
import "fmt"
func main() {zz
    var i interface{} = 5
    pi := &i
    *pi = 10
    fmt.Println(i) // updated
}
// Output: 10