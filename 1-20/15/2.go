package main

import (
	"fmt"
	"strings"
)

func joinWithSeparator(sep string, words ...string) string {
	return strings.Join(words, sep)
}

func main() {
	result := joinWithSeparator("-", "go", "lang", "rocks")
	fmt.Println(result) // Output: go-lang-rocks
}
