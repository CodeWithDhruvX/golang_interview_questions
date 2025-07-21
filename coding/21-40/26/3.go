package main

import "fmt"

func main() {
	arr := [5]int{1, 2, 3, 4, 5}
	slice := arr[1:4]

	fmt.Println("Array length:", len(arr))   // Always 5
	fmt.Println("Array capacity:", cap(arr)) // Always 5

	fmt.Println("Slice length:", len(slice))   // 3
	fmt.Println("Slice capacity:", cap(slice)) // 4
}
