// Turn structs into JSON in Go with just one line!
// Convert a struct to JSON

// Go
package main
import (
    "encoding/json"
    "fmt"
)
type User struct {
    Username string `json:"username"`
}
func main() {
    u := User{"Dave"}
    b, _ := json.Marshal(u)
    fmt.Println(string(b))
}
// Output: {"username":"Dave"}