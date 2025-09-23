package main

import "fmt"

type Point struct {
	X, Y int
}

func main() {
	p := Point{1, 2}
	ptr := &p.X      // get pointer to the struct field
	*ptr++           // increment the actual field via pointer
	fmt.Println(p.X) // Output: 2 ✅
}
