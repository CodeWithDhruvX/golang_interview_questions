# How do you compare two structs?

4. How do you compare two structs?

Opening Hook (0:00–0:10)
"Did you know in Go you can compare two structs with just a simple ==? [pause] But there’s a catch — not all structs can be compared!"

Concept Explanation (0:10–0:40)
"In Go, structs can be compared directly, as long as all of their fields are themselves comparable. For example, integers, strings, and booleans are comparable. But slices, maps, and functions? Nope — those can’t be compared this way. That’s why it’s important to understand where == works and where it doesn’t."

Code Walkthrough (0:40–1:20)
"(show code on screen)
We define a struct Point with two integers: X and Y.
Then, in main, we create two points: p1 := Point{1, 2} and p2 := Point{1, 2}.
Now here’s the cool part — fmt.Println(p1 == p2) prints true. That’s because both fields match exactly.
If we changed one value, like p2.Y = 3, the comparison would return false."

Why It’s Useful (1:20–2:10)
"This comes in handy when you want to check equality of simple structs, like coordinates in a game, or configuration values in a program. But remember — if your struct has a slice or map inside, this won’t work. In those cases, you’d need to write your own comparison logic or use a library."

Outro (2:10–2:30)
"So that’s struct comparison in Go. [pause] Have you ever hit an error because you tried to compare a struct with a slice inside it? Let me know in the comments! And of course, like this video and subscribe for more Go insights."