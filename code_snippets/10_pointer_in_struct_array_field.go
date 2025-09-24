// Increment array fields in structs safely using pointers!
// Pointer in Struct Array Field

// Go
// Problem:
type Data struct { Values [3]int }
d := Data{[3]int{1,2,3}}
for _, v := range d.Values { v++ }
fmt.Println(d.Values) // [1 2 3] ❌

// Solution:
package main
import "fmt"
type Data struct { Values [3]int }
func main() {
    d := Data{[3]int{1,2,3}}
    for i := range d.Values {
        ptr := &d.Values[i]
        *ptr++
    }
    fmt.Println(d.Values)
}
// Output: [2 3 4]