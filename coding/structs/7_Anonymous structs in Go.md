# Anonymous structs in Go

7. Anonymous structs in Go

Opening Hook (0:00–0:10)
"Did you know you can create structs in Go without even giving them a name? [pause] They’re called anonymous structs, and they’re super handy."

Concept Explanation (0:10–0:40)
"Anonymous structs are just like regular structs, except they’re defined on the spot — without creating a new type. They’re lightweight and perfect for temporary data structures when you don’t need to reuse the struct type elsewhere in your program."

Code Walkthrough (0:40–1:20)
"(show code on screen)
Here, inside main, we define user := struct { Name string; Age int }{\"Eve\", 28}.
This creates a one-off struct type with two fields: Name and Age.
We assign values right away — Name is Eve, Age is 28.
Then, fmt.Println(user) prints {Eve 28}. Simple, no fuss."

Why It’s Useful (1:20–2:10)
"Anonymous structs are perfect when you’re working with JSON data quickly, doing quick experiments, or writing unit tests. They keep your code clean because you don’t clutter your project with unnecessary type definitions for data you’ll only use once."

Outro (2:10–2:30)
"So that’s anonymous structs in Go — a quick way to group data without a type. [pause] Have you ever used them before, or do you prefer named structs? Let me know in the comments, and don’t forget to like and subscribe for more Go tips."