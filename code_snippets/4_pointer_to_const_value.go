// ⚡ You Can’t Point to Constants — Here’s the Right Way!
// Both look similar... but one fails before it even runs 👇

package main

import "fmt"

func main() {
	fmt.Println("---- ❌ Problem ----")
	problem()

	fmt.Println("\n---- ✅ Solution ----")
	solution()
}

// ❌ Problem: Trying to take address of a constant
func problem() {
	const x = 10
	ptr := &x
	fmt.Println(*ptr)
	/*
	   // ❌ Compile-time error:
	   // cannot take the address of x (constant)

	*/
	fmt.Println("❌ Compile-time error: cannot take the address of a constant")
}

// ✅ Solution: Use a variable (addressable) instead of a constant
func solution() {
	x := 10         // ✅ variable, not constant
	ptr := &x       // ✅ valid pointer
	*ptr = *ptr + 1 // increment value through pointer
	fmt.Println("Value after increment:", x)
}

// 🧠 Output:
// ---- ❌ Problem ----
// ❌ Compile-time error: cannot take the address of a constant
//
// ---- ✅ Solution ----
// Value after increment: 11
