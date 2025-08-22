// 70% of Go candidates FAIL this pointer vs value receiver trap!
// Pointer vs Value Receiver Trap

// Go
package main
import "fmt"

type User struct { name string }

func (u User) SetNameValue(n string) { u.name = n } // copy
func (u *User) SetNamePointer(n string) { u.name = n } // real

func main() {
    u := User{"Bob"}
    u.SetNameValue("Alice")
    fmt.Println(u.name) // Expected: Alice, Actual: Bob

    u.SetNamePointer("Alice")
    fmt.Println(u.name) // Alice
    // Output:
    // Bob
    // Alice
}