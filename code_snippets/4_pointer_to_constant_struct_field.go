// You can’t point to constants—here’s how to modify fields safely!
// Pointer to Constant Struct Field

// Go
// Problem:
type Config struct { Path string }
constDefault := Config{Path: "/tmp"}
ptr := &constDefault.Path // ❌ illegal

// Solution:
package main
import "fmt"
type Config struct { Path string }
func main() {
    cfg := Config{Path: "/tmp"}
    ptr := &cfg.Path
    *ptr = "/var"
    fmt.Println(cfg.Path)
}
// Output: /var