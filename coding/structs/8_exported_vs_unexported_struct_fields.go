// Why is your JSON empty? Your field isn’t exported!
// Exported vs unexported struct fields

// Go
package main
import (
    "encoding/json"
    "fmt"
)
type Person struct {
    name string // unexported
    Age  int    // exported
}
func main() {
    p := Person{"Frank", 40}
    data, _ := json.Marshal(p)
    fmt.Println(string(data))
}
// Output: {"Age":40} (name missing!)