package main

import (
	"fmt"
)

func mapsEqual(a, b map[string]int) bool {
	if len(a) != len(b) {
		return false
	}
	for k, v := range a {
		if bv, ok := b[k]; !ok || bv != v {
			return false
		}
	}
	return true
}

func main() {
	map1 := map[string]int{"x": 1, "y": 2}
	map2 := map[string]int{"y": 2, "x": 1}

	fmt.Println("Maps equal?", mapsEqual(map1, map2))
}
