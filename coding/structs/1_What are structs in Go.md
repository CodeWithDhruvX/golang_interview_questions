# What are structs in Go?

1. What are structs in Go?

Opening Hook (0:00–0:10)
"Classes don’t exist in Go — so how do you group data? [pause] In Go, the answer is something called a struct, and today I’ll show you exactly how it works."

Concept Explanation (0:10–0:40)
"A struct in Go is short for structure. Think of it like a custom data container where you define fields to store related information. Instead of juggling separate variables like name and age, a struct lets you combine them into one organized type. This makes your code cleaner, easier to maintain, and more powerful."

Code Walkthrough (0:40–1:20)
"(show code on screen)
Here’s our example:
We start with type Person struct { ... }. This defines a new struct type called Person with two fields: a string called Name and an integer called Age.
Next, inside the main function, we create a new Person with p := Person{\"Alice\", 30}. This fills in the fields — Name is Alice, Age is 30.
Finally, fmt.Println(p) prints it out, and we see the output {Alice 30}. [pause] Pretty straightforward!"

Why It’s Useful (1:20–2:10)
"So why use structs? Structs are the foundation of modeling real-world things in Go. Imagine building an e-commerce app — a Product struct could hold price, title, and stock. Or in a game, a Player struct could hold name, health, and score. Basically, any time you need to represent an entity with multiple properties, structs are the tool of choice in Go."

Outro (2:10–2:30)
"So now you know what structs are and how to create them. [pause] What’s the first thing you’d model as a struct in your own code? Let me know in the comments! And don’t forget to like this video and subscribe for more Go tips every week."