package main

import (
	"fmt"
	"sort"
)

func main() {
	scores := map[string]int{
		"Math":    90,
		"Science": 85,
		"English": 88,
	}

	var subjects []string
	for subject := range scores {
		subjects = append(subjects, subject)
	}
	sort.Strings(subjects)

	for _, subject := range subjects {
		fmt.Printf("%s: %d\n", subject, scores[subject])
	}
}
