// Swap variables in Go using pointers—super clean trick!
// Pointer Swapping

// Go
// Problem:
a, b := 1, 2
a, b = b, a // works, but pointers version?

// Solution:
package main
import "fmt"
func swap(x, y *int) {
    *x, *y = *y, *x // swap values
}
func main() {
    a, b := 1, 2
    swap(&a, &b)
    fmt.Println(a, b)
}
// Output: 2 1


