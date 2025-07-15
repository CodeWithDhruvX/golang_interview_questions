package main

import (
	"fmt"
	"time"
)

// Creating a type alias for time.Duration
type MyDuration = time.Duration

func printSleepTime(d MyDuration) {
	fmt.Printf("Sleeping for: %v\n", d)
}

func main() {
	duration := MyDuration(2 * time.Second)
	printSleepTime(duration)
}
