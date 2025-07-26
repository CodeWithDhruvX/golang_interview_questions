✅ 1. Append Doesn't Modify Original Slice
go
Copy
Edit
package main

import "fmt"

func update(s []int) {
	s = append(s, 4) // no effect
}

func main() {
	x := []int{1, 2, 3}
	update(x)
	fmt.Println(x) // [1 2 3]
}
🧠 append() returns a new slice—return it or use reassignment!
🤯 Why didn’t the slice update?

✅ 2. Append Reallocation Visualized
go
Copy
Edit
package main

import "fmt"

func main() {
	s := make([]int, 0, 2)
	s = append(s, 1, 2)
	oldAddr := &s[0]
	s = append(s, 3) // triggers reallocation
	newAddr := &s[0]
	fmt.Println(oldAddr == newAddr) // false
}
💡 Capacity overflow → new memory!
⚠️ Append can silently reallocate!

✅ 3. Nil Slice Panic Danger
go
Copy
Edit
package main

func main() {
	var s []int
	s = append(s, 1) // ✅ OK, not a panic
	_ = s[1]         // ❌ panic: index out of range
}
💡 Always check bounds, even on nil slices.
🚨 Panic on nil or empty slices? Watch this!

✅ 4. Preallocating for Speed
go
Copy
Edit
package main

func main() {
	slow := []int{}
	fast := make([]int, 0, 1000) // preallocate

	for i := 0; i < 1000; i++ {
		slow = append(slow, i)
		fast = append(fast, i)
	}
}
⚡ make([]T, 0, n) = faster appends
🎯 Want faster Go slices? Do this.

✅ 5. Slice vs Array Bug
go
Copy
Edit
package main

import "fmt"

func modify(arr [3]int, s []int) {
	arr[0] = 100     // copy
	s[0] = 100       // shared
}

func main() {
	a := [3]int{1, 2, 3}
	s := []int{1, 2, 3}
	modify(a, s)
	fmt.Println(a) // [1 2 3]
	fmt.Println(s) // [100 2 3]
}
👀 Slices are references, arrays are not!
🧪 Slice vs array: Did you spot the bug?

✅ 6. Append Inside Loop
go
Copy
Edit
package main

import "fmt"

func main() {
	x := []int{}
	for i := 0; i < 3; i++ {
		x = append(x, i)
		fmt.Println(x) // changing backing array
	}
}
💡 Repeated append can mess with memory layout.
🤯 Append inside loop? This will shock you.

✅ 7. One-Liner Multiply with Append
go
Copy
Edit
package main

import "fmt"

func main() {
	nums := []int{1, 2, 3}
	var doubled []int
	for _, v := range nums {
		doubled = append(doubled, v*2) // ✨ one-liner
	}
	fmt.Println(doubled) // [2 4 6]
}
📌 Clean and readable transformation trick.
🧵 This one-liner multiplies your slice!

✅ 8. Append Returns a Copy
go
Copy
Edit
package main

import "fmt"

func addItem(s []int) {
	s = append(s, 99) // new slice
}

func main() {
	x := []int{1, 2}
	addItem(x)
	fmt.Println(x) // [1 2]
}
📌 Always reassign the returned slice!
🔄 Append returns a copy. But why?

✅ 9. Reuse Slice Memory with [:0]
go
Copy
Edit
package main

func main() {
	buf := make([]int, 1000)
	use := buf[:0] // reset but reuse memory
	for i := 0; i < 10; i++ {
		use = append(use, i)
	}
}
💡 Avoids garbage allocation during reuse.
⚡ One trick to make Go slices 🔥 fast

✅ 10. Only One Right Way to Append
go
Copy
Edit
package main

func main() {
	a := []int{}
	// Wrong: a[0] = 1 (panic)
	// Wrong: a = a + 1 (compile error)
	a = append(a, 1) // ✅ correct
}
🎯 Stick to idiomatic slice appending!
📦 3 ways to append — only 1 is safe!