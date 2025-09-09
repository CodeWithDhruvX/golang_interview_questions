// Go
package main

import (
	"fmt"
	"runtime"
)

func printMem(stage string) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	fmt.Printf("%-20s Alloc = %d KB\n", stage, m.Alloc/1024)
}

func main() {
	printMem("Start")

	m := map[int]*[1 << 20]byte{}  // 1MB object
	m2 := map[int]*[1 << 20]byte{} // 1MB object
	m[1] = new([1 << 20]byte)
	printMem("After alloc 1MB")

	// ---- Case 1: delete only ----
	delete(m, 1)
	runtime.GC()
	printMem("After delete only")

	// ---- Case 2: break + delete ----
	m2[1] = new([1 << 20]byte) // allocate again
	printMem("After 2nd alloc")
	m[1] = nil // break reference
	delete(m, 1)
	runtime.GC()
	printMem("After break+delete")
}
