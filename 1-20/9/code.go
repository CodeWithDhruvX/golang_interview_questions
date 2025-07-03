package main

import "fmt"

func init() {
	fmt.Println("Init #1")
}

func init() {
	fmt.Println("Init #2")
}

func main() {
	fmt.Println("Main")
}
