// ⚡ Pointers in Select Statement — Hidden Go Pitfall!
// Both look similar... but only one actually compiles 👇

package main

import (
	"fmt"
	"time"
)

func main() {
	fmt.Println("---- ❌ Problem ----")
	problem()

	fmt.Println("\n---- ✅ Solution ----")
	solution()
}

// ❌ Problem: Taking address of a channel inside select (invalid)
func problem() {
	ch1 := make(chan int)
	ch2 := make(chan int)

	go func() { ch1 <- 5 }()
	go func() { ch2 <- 10 }()

	/*
	   // ❌ Compile-time error:
	   // invalid operation: cannot take the address of ch2
	   select {
	   case val := <-ch1:
	       fmt.Println(&val)
	   case val := <-(&ch2): // ❌ pointer to channel not allowed
	       fmt.Println(val)
	   }
	*/

	fmt.Println("❌ Compile-time error: cannot take address of channel in select")
}

// ✅ Solution: Use pointer of received value, not of the channel
func solution() {
	ch1 := make(chan int)
	ch2 := make(chan int)

	go func() { ch1 <- 5 }()
	go func() { ch2 <- 10 }()

	// First select — whichever channel is ready first
	select {
	case val := <-ch1:
		fmt.Println("Received from ch1, pointer:", &val, "value:", val)
	case val := <-ch2:
		fmt.Println("Received from ch2, value:", val)
	}

	// Wait and demonstrate the other channel as well
	time.Sleep(100 * time.Millisecond)

	// Second round to show both channels clearly
	go func() { ch1 <- 15 }()
	go func() { ch2 <- 20 }()

	select {
	case val := <-ch1:
		fmt.Println("Received from ch1, pointer:", &val, "value:", val)
	case val := <-ch2:
		fmt.Println("Received from ch2, value:", val)
	}
}

// 🧠 Output Example:
// ---- ❌ Problem ----
// ❌ Compile-time error: cannot take address of channel in select
//
// ---- ✅ Solution ----
// Received from ch1, pointer: 0xc0000180a8 value: 5
// Received from ch2, value: 20
