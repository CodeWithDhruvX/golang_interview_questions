package main

import (
	"fmt"
	"strconv"
	"strings"
)

func sliceKey(s []int) string {
	strs := make([]string, len(s))
	for i, val := range s {
		strs[i] = strconv.Itoa(val)
	}
	return strings.Join(strs, ",")
}

func main() {
	m := make(map[string]string)
	s1 := []int{1, 2, 3}
	s2 := []int{4, 5, 6}

	m[sliceKey(s1)] = "first"
	m[sliceKey(s2)] = "second"

	fmt.Println("Key 1:", m[sliceKey(s1)])
	fmt.Println("Key 2:", m[sliceKey(s2)])
}
