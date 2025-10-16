// You can even use pointers to channels — here’s how!
// Topic: Pointer to Channel

// ---------------- PROBLEM ----------------
package main

import "fmt"

func problem() {
	// ch := make(chan int)
	// ptr := &ch // pointer to channel

	// // Trying to send directly using the pointer
	// // — ❌ not allowed
	// *ptr <- 10 // uncommenting this will cause confusion for most beginners

	// fmt.Println("Problem: You can't directly send using pointer to channel!")
}

// ---------------- SOLUTION ----------------
func send(ch *chan int, val int) {
	*ch <- val // send via pointer
}

func solution() {
	ch := make(chan int)
	go func() {
		send(&ch, 42)
	}()
	fmt.Println("Solution Output:", <-ch) // ✅ Output: 42
}

func main() {
	problem()
	solution()
}
