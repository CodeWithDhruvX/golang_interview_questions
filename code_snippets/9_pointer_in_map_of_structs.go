// Updating struct values in maps? Pointers fix it instantly!
// Pointer in Map of Structs

// Go
// Problem:
m := map[string]Point{"a":{1,2}}
p := m["a"]
p.X++
fmt.Println(m["a"].X) // 1 ❌ not updated

// Solution:
package main
import "fmt"
type Point struct { X,Y int }
func main() {
    m := map[string]*Point{"a":{1,2}}
    m["a"].X++
    fmt.Println(m["a"].X)
}
// Output: 2


give two seperate code snippet