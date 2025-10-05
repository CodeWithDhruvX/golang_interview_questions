package main

import "fmt"

// ----------------------------
// ❌ Problem: Swapping without pointers
// ----------------------------
func swapProblem(x, y int) {
	x, y = y, x                              // only swaps local copies
	fmt.Println("Inside swapProblem:", x, y) // swapped inside function
}

func problem() {
	fmt.Println("=== Problem ===")
	a, b := 1, 2
	swapProblem(a, b)
	fmt.Println("Outside swapProblem:", a, b) // ❌ values unchanged: 1 2
}

// ----------------------------
// ✅ Solution: Swapping with pointers
// ----------------------------
func swapSolution(x, y *int) {
	*x, *y = *y, *x // swaps actual values via pointers
}

func solution() {
	fmt.Println("=== Solution ===")
	a, b := 1, 2
	swapSolution(&a, &b)
	fmt.Println("After swapSolution:", a, b) // ✅ values swapped: 2 1
}

func main() {
	problem()
	solution()
}
