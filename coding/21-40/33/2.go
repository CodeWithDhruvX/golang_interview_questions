package main

import (
	"fmt"
)

func main() {
	countries := map[string]string{
		"US": "United States",
		"IN": "India",
		"JP": "Japan",
	}

	for code := range countries {
		fmt.Printf("Country code %s represents %s\n", code, countries[code])
	}
}
