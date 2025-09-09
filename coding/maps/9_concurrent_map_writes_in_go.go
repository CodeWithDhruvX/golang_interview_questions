// problem:

// package main

// import (
// 	"fmt"
// 	"sync"
// )

// func main() {
// 	m := make(map[string]int)
// 	var wg sync.WaitGroup
// 	wg.Add(2)

// 	// Goroutine 1
// 	go func() {
// 		defer wg.Done()
// 		for i := 0; i < 100000; i++ {
// 			m["a"] = i // concurrent write
// 		}
// 	}()

// 	// Goroutine 2
// 	go func() {
// 		defer wg.Done()
// 		for i := 0; i < 100000; i++ {
// 			m["b"] = i // concurrent write
// 		}
// 	}()

// 	wg.Wait()
// 	fmt.Println(m) // often crashes: fatal error: concurrent map writes
// }

// solution:

package main

import (
	"fmt"
	"sync"
)

func main() {
	var m sync.Map
	var wg sync.WaitGroup
	wg.Add(2)

	// Goroutine 1
	go func() {
		defer wg.Done()
		for i := 0; i < 100000; i++ {
			m.Store("a", i) // safe write
		}
	}()

	// Goroutine 2
	go func() {
		defer wg.Done()
		for i := 0; i < 100000; i++ {
			m.Store("b", i) // safe write
		}
	}()

	wg.Wait()

	// Safe reads
	if v, ok := m.Load("a"); ok {
		fmt.Println("a:", v)
	}
	if v, ok := m.Load("b"); ok {
		fmt.Println("b:", v)
	}
}
