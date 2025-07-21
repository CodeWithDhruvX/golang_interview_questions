package main

import (
	"fmt"
	"sort"
)

func main() {
	m := map[string]int{"banana": 3, "apple": 2, "cherry": 5}

	// Extract and sort keys
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	// Print in sorted key order
	for _, k := range keys {
		fmt.Printf("%s: %d\n", k, m[k])
	}
}
