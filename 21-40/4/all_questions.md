✅ 1. Copying slices in Go: Are you doing it wrong?
go
Copy
Edit
package main
import "fmt"

func main() {
	a := []int{1, 2, 3}
	b := a            // ❌ Not a real copy
	b[0] = 99         // changes 'a' too!

    fmt.Println(a)    // [99 2 3] ❗

    c := make([]int, len(a))
	copy(c, a)        // ✅ Actual copy
	c[1] = 77         // doesn't affect 'a'

    fmt.Println(a)    // [99 2 3]
	fmt.Println(c)    // [99 77 3]
}
🧠 🤯 Why did the array value change too?

✅ 2. Go slices vs arrays: One costly mistake
go
Copy
Edit
package main
import "fmt"

func main() {
	arr := [3]int{1, 2, 3}
	slc := arr[0:2] // slice from array

    fmt.Println(len(slc)) // 2
	fmt.Println(cap(slc)) // 3 ⚠️ full backing array

    slc = append(slc, 9)  // modifies 'arr'!
	fmt.Println(arr)      // [1 2 9]
}
🧠 😱 Did append mutate the array?

✅ 3. Append in Go is not what you think!
go
Copy
Edit
package main
import "fmt"

func main() {
	a := []int{1, 2}
	b := a

    b = append(b, 3) // reallocates slice
	b[0] = 99

    fmt.Println(a)   // [1 2] ✅ unchanged
	fmt.Println(b)   // [99 2 3]
}
🧠 👀 Is your append mutating the original?

✅ 4. Slice length vs capacity: Interview trap!
go
Copy
Edit
package main
import "fmt"

func main() {
	s := make([]int, 2, 5) // len=2, cap=5
	fmt.Println(len(s))    // 2
	fmt.Println(cap(s))    // 5

    s = append(s, 1, 2, 3) // fills capacity
	fmt.Println(s)         // [0 0 1 2 3]
}
🧠 🎯 Can you predict cap after next append?

✅ 5. Modify slice inside a function: Why it fails!
go
Copy
Edit
package main
import "fmt"

func addItem(s []int) {
	s = append(s, 99) // new slice, not returned
}

func main() {
	x := []int{1, 2}
	addItem(x)

    fmt.Println(x) // [1 2] ❌ no change!
}
🧠 🤔 Why didn’t the slice get updated?

✅ 6. The hidden cost of copying large slices
go
Copy
Edit
package main
import "fmt"

func main() {
	a := make([]int, 1e6) // large slice
	b := a                // just a reference!

    b[0] = 42             // affects 'a'
	fmt.Println(a[0])     // 42 ✅

    c := make([]int, len(a))
	copy(c, a)            // deep copy

    c[1] = 99
	fmt.Println(a[1])     // 0 ✅ not affected
}
🧠 📉 Shallow copy = performance drain?

✅ 7. Cutting slices the RIGHT way
go
Copy
Edit
package main
import "fmt"

func main() {
	a := []int{1, 2, 3, 4, 5}

    // Remove index 2 (value 3)
	a = append(a[:2], a[3:]...)

    fmt.Println(a) // [1 2 4 5] ✅
}
🧠 ✂️ Are you slicing cleanly like this?

✅ 8. Slices as parameters: Dangerous default behavior
go
Copy
Edit
package main
import "fmt"

func modify(s []int) {
	s[0] = 99 // modifies original!
}

func main() {
	x := []int{1, 2, 3}
	modify(x)
	fmt.Println(x) // [99 2 3] ⚠️
}
🧠 😲 Did that function just mutate your data?

✅ 9. Slice memory leaks in Go (real bug)
go
Copy
Edit
package main
import "fmt"

func main() {
	huge := make([]byte, 1e6)
	small := huge[:10]     // keeps ref to 1MB

    fmt.Println(len(small)) // 10
	huge = nil              // GC can't reclaim full slice
}
🧠 🧠 Is a 10-byte slice leaking 1MB?

✅ 10. Make vs new: What should you use for slices?
go
Copy
Edit
package main
import "fmt"

func main() {
	a := make([]int, 3) // ✅ correct way
	fmt.Println(a)      // [0 0 0]

    // b := new([]int)  // avoid for slices
}
🧠 🛠️ Still using new instead of make?
