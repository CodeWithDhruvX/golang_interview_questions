// Forgot struct tags? That’s why your JSON is empty!
// How do you define and use struct tags?

// Go
package main
import (
    "encoding/json"
    "fmt"
)
type Person struct {
    Name string `json:"name"`
    Age  int    `json:"age"`
}
func main() {
    p := Person{"Bob", 25}
    data, _ := json.Marshal(p)
    fmt.Println(string(data))
}
// Output: {"name":"Bob","age":25}