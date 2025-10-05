package main

import "fmt"

func main() {
	fmt.Println("=== Problem: Pointers in range ===")
	m1 := map[string]int{"x": 1, "y": 2}
	for _, v := range m1 {
		ptr := &v // pointer to loop variable (copy!)
		*ptr *= 2 // modifies the copy, not the map
	}
	fmt.Println("Map after loop:", m1) // unchanged ❌

	fmt.Println("\n=== Solution: Direct map update ===")
	m2 := map[string]int{"x": 1, "y": 2}
	for k := range m2 {
		m2[k] *= 2 // directly updates the map
	}
	fmt.Println("Map after loop:", m2) // updated ✅
}
