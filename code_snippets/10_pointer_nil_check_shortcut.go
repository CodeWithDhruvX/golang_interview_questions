package main

import "fmt"

func main() {
	var ptr *int
	fmt.Println(func() int {
		if ptr != nil {
			return *ptr
		}
		return 0 // default value
	}())
}

// Output: 0
