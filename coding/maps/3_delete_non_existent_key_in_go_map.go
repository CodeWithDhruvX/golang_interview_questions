// What happens if you delete a key that doesn’t exist in Go?
// Delete Non-Existent Key in Go Map

// Go
package main
import "fmt"

func main() {
    m := map[string]int{"x": 10}
    delete(m, "y") // safe delete
    fmt.Println(m)
    // Output: map[x:10]
}