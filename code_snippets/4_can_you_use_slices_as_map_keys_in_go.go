// This is the #1 interview trap question in Go!
// Can You Use Slices as Map Keys in Go?

// Go
// Problem:
// package main

// import "fmt"

// func main() {
// 	s := []int{1, 2}
// 	m := map[[]int]string{s: "value"} // panic
// 	fmt.Println(m)
// }

// Solution:
package main

import "fmt"

func main() {
	// Only comparable types allowed
	s := []int{1, 2}
	str := fmt.Sprint(s)
	m := map[string]string{str: "value"} // slice converted to string
	fmt.Println(m)                       // Output: map[1,2:value]
}
