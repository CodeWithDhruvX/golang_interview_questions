package main

import (
	"fmt"
	"os"
)

func main() {
	file, err := os.Open("data.txt")
	if err != nil {
		fmt.Println("Error opening file:", err)
		return
	}
	defer file.Close() // Ensures file is closed when function ends

	fmt.Println("Reading file... (Imagine logic here)")
}
