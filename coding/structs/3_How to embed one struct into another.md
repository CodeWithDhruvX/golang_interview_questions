# How to embed one struct into another?

3. How to embed one struct into another?

Opening Hook (0:00–0:10)
"Inheritance doesn’t exist in Go… but embedding does! [pause] Let me show you how you can reuse and extend structs without traditional classes."

Concept Explanation (0:10–0:40)
"In Go, instead of using inheritance like in Java or Python, we use composition. Struct embedding is one of the easiest ways to achieve this. It lets you place one struct inside another, and the inner fields can be accessed almost as if they were part of the outer struct."

Code Walkthrough (0:40–1:20)
"(show code on screen)
We start with a simple struct Person that has a Name field.
Then we define an Employee struct. Inside it, we embed Person directly, without giving it a field name. That’s struct embedding.
In main, we create an Employee using Employee{Person{\"Carol\"}, 101}.
When we print e.Name and e.ID, it works seamlessly. The embedded struct’s Name is directly accessible on the outer struct."

Why It’s Useful (1:20–2:10)
"Embedding is powerful because it promotes composition over inheritance. Let’s say you have a Person struct, and you want different roles like Employee, Manager, or Student. Instead of duplicating code, you embed Person in each. It keeps your code modular, flexible, and easy to extend. This is especially important in Go, where simplicity and clarity are core principles."

Outro (2:10–2:30)
"So that’s struct embedding in Go — a clean way to reuse code without messy hierarchies. [pause] What’s one real-world example where you’d use embedding? Share it in the comments! And if you enjoyed this, don’t forget to like and subscribe for more Go tutorials."