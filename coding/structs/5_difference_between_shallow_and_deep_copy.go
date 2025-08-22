// Copying a struct with slices? Careful — it’s only shallow!
// Difference between shallow and deep copy?

// Go
package main
import "fmt"
type Data struct {
    Values []int
}
func main() {
    d1 := Data{[]int{1, 2}}
    d2 := d1 // shallow copy
    d2.Values[0] = 99
    fmt.Println(d1.Values) // Expected [1 2], Actual [99 2]
}
// Output: [99 2] (pitfall!)