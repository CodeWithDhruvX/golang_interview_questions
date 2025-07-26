✅ Question 1
“Arrays vs Slices: Why most Go devs get this WRONG!”
🧠 Tip: Slices are references, not actual data!

go
Copy
Edit
package main

import "fmt"

func main() {
	arr := [3]int{1, 2, 3}  // Array: fixed-size
	slc := arr[:]           // Slice: view of array

	slc[0] = 99             // Modify slice

	fmt.Println(arr)        // [99 2 3]
	fmt.Println(slc)        // [99 2 3]
}
🔁 🤯 Why did the array value change too?

✅ Question 2
“This Go mistake can crash your backend!”
🧠 Tip: Arrays are value types; slices are references.

go
Copy
Edit
package main

import "fmt"

func resizeArray(arr [3]int) {
	arr[0] = 42             // Modify copy
}

func resizeSlice(slc []int) {
	slc[0] = 42             // Modify shared data
}

func main() {
	a := [3]int{1, 2, 3}
	s := []int{1, 2, 3}

	resizeArray(a)
	resizeSlice(s)

	fmt.Println(a)          // [1 2 3]
	fmt.Println(s)          // [42 2 3]
}
🧠 👍 Like if you’ve done this!

✅ Question 3
“If you answer this wrong, you fail the Go interview.”
🧠 Tip: Slices have internal pointer + len + cap.

go
Copy
Edit
package main

import "fmt"

func main() {
	s := []int{1, 2, 3, 4}
	fmt.Println(len(s), cap(s)) // 4 4

	s = s[:2]                   // Slice shrink
	fmt.Println(len(s), cap(s)) // 2 4
}
🧐 🚀 Watch next: Go memory management explained

✅ Question 4
“Why slices in Go are secretly dangerous.”
🧠 Tip: Use copy() before passing to goroutines.

go
Copy
Edit
package main

import "fmt"

func modify(s []int) {
	s[0] = 99                // Modify shared
}

func main() {
	orig := []int{1, 2, 3}
	mod := orig              // Shared slice

	modify(mod)

	fmt.Println(orig)        // [99 2 3] - Oops!
}
🔁 🔁 Share this with your team

✅ Question 5
“Are slices passed by value or reference?”
🧠 Tip: Passed by value, but share backing array.

go
Copy
Edit
package main

import "fmt"

func change(s []int) {
	s[0] = 10                // Affects original
}

func main() {
	data := []int{1, 2, 3}
	change(data)

	fmt.Println(data)        // [10 2 3]
}
❓ 🤔 So… are slices passed by reference or not?

Let me know if you'd like:

Carousel-optimized captions for Instagram/LinkedIn

Thumbnail hooks

Matching voiceover script

Code image exports with styling

Or more questions turned into snippets in bulk

Just drop the next batch of questions when you're ready.







You said:
I have a list of technical interview questions. For each question, I want you to generate a compact, visually appealing code snippet that can be used in YouTube Shorts or carousel posts. Follow these rules strictly:

---

🎯 FORMAT FOR EACH QUESTION:

**1. Code Snippet Block**  
- Language: Go (or use Python/JavaScript if specified)
- Must be SHORT and fit in 20–25 seconds of reading time
- Should include clear, minimal inline comments (1–3 words only)
- Demonstrate the key difference, concept, or common pitfall
- Highlight the *Expected vs Actual Output* if relevant
- Self-contained (no unnecessary external packages)

**2. Retention Hook (1 line)**  
- A short line/question at the bottom that makes the user think or want to rewatch  
Example:  
🤯 Why did the array value change too?

---

📥 **Input: Bulk Questions (like below)**  
plaintext
6	“What happens when you append to a slice?”	Problem: Memory reallocation, hidden cost.
Solution: It might create a new array.
Tip: Preallocate with make([]T, len, cap)	👀 Watch till end for bonus hack
7	“Go arrays are not what you think…”	Problem: You think they behave like slices.
Solution: Arrays are fixed and copied.
Tip: Don’t return arrays from functions.	✅ Subscribe for Go concepts daily
8	“90% of devs can’t guess the output of this Go code!”	Problem: Show code using slices & arrays.
Solution: Explain why output is unexpected.
Tip: Show behavior of len and cap.	🤯 Comment your guess before answer
9	“Slices vs Arrays in Go – Animated in 30 sec!”	Problem: Concept is confusing without visuals.
Solution: Show animated memory layout.
Tip: Explain pointers visually.	🎯 Rewatch to grasp it fully
10	“This slice bug took down our Go service for 2 hours.”	Problem: Unexpected behavior with shared slice.
Solution: Use deep copy before passing.
Tip: Monitor slice capacity during append.	🔁 Share if you’ve faced similar bugs


ChatGPT said:
Absolutely Dhruv! Here's Batch 2 of compact, clean, and YouTube Shorts–ready code snippets based on your next 5 technical interview prompts — optimized for carousel posts, Shorts, and interviews.

✅ Question 6
“What happens when you append to a slice?”
🧠 Tip: It might create a new array!

go
Copy
Edit
package main

import "fmt"

func main() {
	s1 := []int{1, 2, 3}
	s2 := s1            // Share backing array

	s1 = append(s1, 4)  // Realloc if cap exceeded
	s2[0] = 99          // Modify original

	fmt.Println(s1)     // [1 2 3 4]
	fmt.Println(s2)     // [99 2 3]
}
👀 👀 Watch till end for bonus hack

✅ Question 7
“Go arrays are not what you think…”
🧠 Tip: Don’t return arrays from functions!

go
Copy
Edit
package main

import "fmt"

func getArray() [3]int {
	arr := [3]int{1, 2, 3}
	return arr            // Copied, not referenced
}

func main() {
	a1 := getArray()
	a2 := a1              // Full copy
	a2[0] = 99

	fmt.Println(a1)       // [1 2 3]
	fmt.Println(a2)       // [99 2 3]
}
✅ ✅ Subscribe for Go concepts daily

✅ Question 8
“90% of devs can’t guess the output of this Go code!”
🧠 Tip: Show behavior of len and cap.

go
Copy
Edit
package main

import "fmt"

func main() {
	a := [5]int{1, 2, 3, 4, 5}
	s := a[1:4]            // [2 3 4]

	fmt.Println(len(s))   // 3
	fmt.Println(cap(s))   // 4 (from index 1 to end)
}
🤯 🤯 Comment your guess before answer

✅ Question 9
“Slices vs Arrays in Go – Animated in 30 sec!”
🧠 Tip: Explain pointers visually.

go
Copy
Edit
package main

import "fmt"

func main() {
	arr := [3]int{1, 2, 3} // Stored on stack
	slc := arr[:]          // Slice → pointer to arr

	slc[1] = 99

	fmt.Println(arr)       // [1 99 3]
	fmt.Println(slc)       // [1 99 3]
}
🎯 🎯 Rewatch to grasp it fully

✅ Question 10
“This slice bug took down our Go service for 2 hours.”
🧠 Tip: Monitor slice capacity during append.

go
Copy
Edit
package main

import "fmt"

func main() {
	orig := []int{1, 2, 3}
	copied := make([]int, len(orig))
	copy(copied, orig)     // Deep copy

	orig = append(orig, 4) // May realloc
	copied[0] = 99

	fmt.Println(orig)      // [1 2 3 4]
	fmt.Println(copied)    // [99 2 3]
}
🧨 🔁 Share if you’ve faced similar bugs

🔥 Want carousel layout text or Shorts overlay design too?
Just let me know — or drop the next batch (11–15) and I’ll keep building.