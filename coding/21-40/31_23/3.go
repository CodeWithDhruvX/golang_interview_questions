package main

import (
	"encoding/json"
	"fmt"
)

func mapsEqualJSON(a, b map[string]int) bool {
	aj, _ := json.Marshal(a)
	bj, _ := json.Marshal(b)
	return string(aj) == string(bj)
}

func main() {
	map1 := map[string]int{"a": 1, "b": 2}
	map2 := map[string]int{"b": 2, "a": 1}

	if mapsEqualJSON(map1, map2) {
		fmt.Println("Maps are equal")
	} else {
		fmt.Println("Maps are not equal")
	}
}
