### Snippet 1: Basic Named Return with Computation

```go
package main

import "fmt"

func add(a, b int) (sum int) {
	sum = a + b
	return
}

func main() {
	result := add(10, 15)
	fmt.Println("Sum is:", result)
}
```

### Script (Snippet 1)

> Okay friends, let's understand this simple Go code using **named return values**.
> This is one of those things in Go that makes your function **shorter and cleaner**, especially when you’re returning just one or two values.

> The function `add()` takes two integers: `a` and `b`. We’ve already **named the return value** as `sum` in the function signature. Inside the function, we assign `sum = a + b` and return — Go understands we're returning `sum`.

> In `main()`, we call `add(10, 15)` and print the result. So it’ll say: `Sum is: 25`.

> When to use? For small utility functions — short, readable, and clean!

---

### Snippet 2 (Updated): Named Return in Error Handling

```go
package main

import (
	"errors"
	"fmt"
)

func divide(a, b int) (result int, err error) {
	if b == 0 {
		err = errors.New("cannot divide by zero")
		return
	}
	result = a / b
	return
}

func main() {
	value, err := divide(20, 0)
	if err != nil {
		fmt.Println("Error:", err)
		return
	}
	fmt.Println("Result is:", value)
}
```

### Script (Snippet 2)

> Here we have a function that divides two integers and handles division by zero.

> The function `divide()` returns both `result` and `err`, both named. If the denominator is zero, we assign an error to `err` and just return. Otherwise, we compute and assign `result = a / b`, and return.

> In `main()`, we call it and check `err` — if there’s an error, we print it; otherwise, we print the result.

> This is how most Go standard library functions are structured — it's clean, predictable, and safe for production code.

---

### Snippet 3: Conditional Logic with Named Return

```go
package main

import "fmt"

func getStatus(score int) (status string) {
	if score >= 75 {
		status = "Distinction"
		return
	} else if score >= 40 {
		status = "Pass"
		return
	}
	status = "Fail"
	return
}

func main() {
	fmt.Println("Student Status:", getStatus(82))
}
```

### Script (Snippet 3)

> This one feels like a college grading system. We return a student’s result — "Distinction", "Pass", or "Fail" — based on marks using named return `status`.

> The function `getStatus()` returns a named string. Inside, we use conditionals and assign directly to `status`, and then simply `return`. No need to pass the value to `return` manually.

> Clean logic, very readable, and very Go-style.

> Great for condition-based messaging, grading systems, and status responses in APIs.

---

### Thumbnail Titles (Plain Text)

* Go Named Return Usecase
* Go Named Return Error Handling
* Go Named Return Condition Logic

---

### Final JSON Array for All 3 Snippets

```json
[
  {
    "videoFile": "C:/Users/dhruv/Videos/2025/golang_interview_questions/11/coding_shorts/audio/2025-07-10 22-02-26_output.mp4",
    "title": "Master Named Return in Go 🔁 Clean & Idiomatic Coding",
    "description": "\u2705 Learn what Named Return Values are in Golang with this easy, beginner-friendly explanation!\n\n\ud83d\udc68\u200d\ud83c\udfeb In this short, we cover:\n- What are named return values?\n- How they make your Go code cleaner\n- Real-world use cases (like backend microservices)\n- A line-by-line walkthrough of a simple function\n\n\ud83c\udfaf Perfect for:\n- Golang interview preparation\n- Backend developers\n- Students learning Go\n\n\ud83d\udccc Don't miss the upcoming videos in this Golang Interview Series!\n\n#golang #golanginterview #go #namedreturn #golangshorts #backenddeveloper #interviewprep",
    "tags": [
      "golang",
      "go programming",
      "named return values",
      "golang for beginners",
      "golang interview questions",
      "backend development",
      "go function return",
      "clean go code"
    ],
    "categoryName": "Education",
    "privacyStatus": "private",
    "thumbnail": "C:/Users/dhruv/Videos/2025/golang_interview_questions/11/thumbnail_named_return.png",
    "playlistName": "Golang Interview Shorts 🔥 | 1 Go Qn a Day | Crack Interviews Fast",
    "publishAt": "2025-07-20 09:00:00",
    "madeForKids": false,
    "ageRestriction": false
  },
  {
    "videoFile": "C:/Users/dhruv/Videos/2025/golang_interview_questions/11/coding_shorts/audio/2025-07-10 22-02-26_output.mp4",
    "title": "Golang Interview Prep 🎯 Named Returns + Error Handling Explained!",
    "description": "🚨 Learn how Named Return Values work with Error Handling in Golang — a real-world and interview-worthy pattern!\n\n\ud83d\udc68\u200d\ud83c\udfeb In this short video:\n- How to return both result and error using named values\n- Common Go idioms in real apps (API, file, math)\n- Step-by-step breakdown of a divide function\n- Error check for divide-by-zero\n\n💼 Perfect for:\n- Backend developers\n- Go interview candidates\n- Anyone building real-world Go code\n\n#golang #errorhandling #golanginterview #namedreturn #backenddeveloper #go #golangtips",
    "tags": [
      "golang",
      "go language",
      "error handling",
      "named return in go",
      "golang for backend",
      "golang interview questions",
      "go function return",
      "go idioms"
    ],
    "categoryName": "Education",
    "privacyStatus": "private",
    "thumbnail": "C:/Users/dhruv/Videos/2025/golang_interview_questions/11/thumbnail_named_return_error.png",
    "playlistName": "Golang Interview Shorts 🔥 | 1 Go Qn a Day | Crack Interviews Fast",
    "publishAt": "2025-07-21 09:00:00",
    "madeForKids": false,
    "ageRestriction": false
  },
  {
    "videoFile": "C:/Users/dhruv/Videos/2025/golang_interview_questions/11/coding_shorts/audio/2025-07-10 22-02-26_output.mp4",
    "title": "Golang Named Return 📘 Use If-Else Like a Pro",
    "description": "🎓 Understand how to use Named Return Values in Golang with clean if-else logic — just like real-life grading systems!\n\n📚 In this short tutorial:\n- How to return based on conditions using named values\n- Distinction, Pass, Fail example\n- Clean Go coding with no repetition\n- Practical Go for interviews and backend apps\n\n💡 Use this for:\n- Scoring logic\n- Role levels\n- Status labels in APIs\n\n#golang #go #golanginterview #namedreturn #goifelse #interviewprep #golangshorts #goconditional",
    "tags": [
      "golang",
      "go programming",
      "named return",
      "if else golang",
      "golang short video",
      "golang interview",
      "backend logic go",
      "golang patterns"
    ],
    "categoryName": "Education",
    "privacyStatus": "private",
    "thumbnail": "C:/Users/dhruv/Videos/2025/golang_interview_questions/11/thumbnail_named_return_conditional.png",
    "playlistName": "Golang Interview Shorts 🔥 | 1 Go Qn a Day | Crack Interviews Fast",
    "publishAt": "2025-07-22 09:00:00",
    "madeForKids": false,
    "ageRestriction": false
  }
]
```
