package main

import "fmt"

func printMarks(marks ...int) {
	for i, mark := range marks {
		fmt.Printf("Subject %d: %d marks\n", i+1, mark)
	}
}

func main() {
	subjectMarks := []int{78, 85, 92, 88}
	printMarks(subjectMarks...)
}
