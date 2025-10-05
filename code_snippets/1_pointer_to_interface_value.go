package main

import "fmt"

func main() {
	// ----------------------------
	// ❌ Problem: Pointer to Interface
	// ----------------------------
	fmt.Println("=== Problem: Pointer to Interface ===")
	a := 5
	var i interface{} = a // interface holds a copy of 'a'
	pi := &i              // pointer to interface

	*pi = 10              // update interface
	fmt.Println("a =", a) // original variable unchanged
	fmt.Println("i =", i) // interface updated

	fmt.Println()

	// ----------------------------
	// ✅ Solution: Pointer to Concrete Value
	// ----------------------------
	fmt.Println("=== Solution: Pointer to Concrete Value ===")
	b := 5
	var j interface{} = &b // interface holds pointer to 'b'

	*(j.(*int)) = 10      // safely update underlying value
	fmt.Println("b =", b) // original variable updated
	fmt.Println("j =", j) // interface updated
}
