package main

import "fmt"

func main() {
	for i := 1; i <= 5; i++ {
		if i == 3 {
			continue
		}
		if i == 5 {
			break
		}
		fmt.Println(i)
	}
}
