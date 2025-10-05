package main

import "fmt"

// ----------------------------
// ❌ Problem: Pointer to a copy inside struct
// ----------------------------
type Inner struct {
	Val int
}
type Outer struct {
	I Inner
}

func problem() {
	fmt.Println("=== Problem ===")
	o := Outer{Inner{10}}
	innerCopy := o.I      // this is a COPY of Inner
	ptr := &innerCopy.Val // pointer points to the copy
	*ptr = 99
	fmt.Println("o.I.Val (expected 99?):", o.I.Val) // 10 ❌ value not updated
}

// ----------------------------
// ✅ Solution: Pointer to original nested struct
// ----------------------------
func solution() {
	fmt.Println("=== Solution ===")
	o := Outer{Inner{10}}
	ptr := &o.I.Val // pointer points to original value
	*ptr = 99
	fmt.Println("o.I.Val (updated correctly):", o.I.Val) // 99 ✅ value updated
}

func main() {
	problem()
	solution()
}
