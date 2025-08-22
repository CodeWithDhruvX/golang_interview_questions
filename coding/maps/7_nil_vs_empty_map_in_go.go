// This Go map question fails 70% of interviews: nil vs empty!
// Nil vs Empty Map in Go

// Go
package main
import "fmt"

func main() {
    var nilMap map[string]int
    emptyMap := make(map[string]int)
    fmt.Println(nilMap == nil)
    fmt.Println(emptyMap == nil)
    // Output: true \n false
}