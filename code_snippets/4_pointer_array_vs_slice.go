// ⚡ Slices Share Arrays — Avoid Surprises with a Simple Copy Trick!
// Both outputs may *look fine*, but only one keeps your data safe 👇

package main

import "fmt"

func main() {
	fmt.Println("---- ❌ Problem ----")
	problem()

	fmt.Println("\n---- ✅ Solution ----")
	solution()
}

// ❌ Problem: Slice shares the same underlying array
func problem() {
	arr := [3]int{1, 2, 3}
	slice := arr[:] // shares same memory
	slice[0] = 99   // modifies arr too
	fmt.Println("Slice:", slice)
	fmt.Println("Array:", arr)
	fmt.Println("⚠️ Slice and array share memory — arr changed!")
}

// ✅ Solution: Make a copy to keep array safe
func solution() {
	arr := [3]int{1, 2, 3}
	slice := make([]int, len(arr))
	copy(slice, arr[:]) // ✅ independent copy
	slice[0] = 99
	fmt.Println("Slice:", slice)
	fmt.Println("Array:", arr)
	fmt.Println("✅ Original array untouched — slice is independent")
}

// 🧠 Output:
// ---- ❌ Problem ----
// Slice: [99 2 3]
// Array: [99 2 3]
// ⚠️ Slice and array share memory — arr changed!
//
// ---- ✅ Solution ----
// Slice: [99 2 3]
// Array: [1 2 3]
// ✅ Original array untouched — slice is independent
