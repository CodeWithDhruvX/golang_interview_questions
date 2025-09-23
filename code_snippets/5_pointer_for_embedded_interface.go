// Pointers to embedded interfaces let you call methods properly!
// Pointer for Embedded Interface

// Go
// Problem:
type Logger interface { Log() }
type Service struct { Logger }
var s Service
// cannot call pointer methods directly

// Solution:
package main
import "fmt"
type Logger interface { Log() }
type Service struct { Logger }
type MyLog struct {}
func (m *MyLog) Log() { fmt.Println("logged") }
func main() {
    s := Service{Logger: &MyLog{}}
    s.Log()
}
// Output: logged