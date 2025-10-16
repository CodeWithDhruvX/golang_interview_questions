// Want to update array elements efficiently? Pointers to the rescue!
// Topic: Pointer to Array Element

// ---------------- PROBLEM ----------------
package main

import "fmt"

func problem() {
	arr := [3]int{1, 2, 3}
	ptr := &arr[0] // pointer to first element
	*ptr = 2       // modifies only arr[0]
	fmt.Println("Problem Output:", arr)
}

// ---------------- SOLUTION ----------------
func solution() {
	arr := [3]int{1, 2, 3}
	for i := range arr {
		ptr := &arr[i] // pointer to each element
		*ptr *= 2
	}
	fmt.Println("Solution Output:", arr)
}

func main() {
	problem()
	solution()
}
