// Ever seen ‘fatal error: concurrent map writes’? Here’s the fix!
// Concurrent Map Writes in Go

// Go
package main
import (
    "fmt"
    "sync"
)

func main() {
    var m sync.Map
    m.Store("a", 1)
    v, _ := m.Load("a")
    fmt.Println(v)
    // Output: 1
}