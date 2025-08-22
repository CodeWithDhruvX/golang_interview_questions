# Go Methods with Interfaces

7. Go Methods with Interfaces

Opening Hook (0:00–0:10)
“Go doesn’t need classes to give you power. [pause] With methods and interfaces, Go lets you write flexible, reusable code — and it’s way simpler than you think.”

Concept Explanation (0:10–0:40)
“In Go, interfaces define behavior, not structure. [pause] If a type implements all the methods an interface requires, it automatically satisfies that interface — no extra keywords or declarations needed. [pause] This is one of Go’s most powerful and elegant features.”

Code Walkthrough (0:40–1:20)
(show code on screen)
“Here’s a simple example. We define an interface called Speaker with one method: Speak() string.
Then, we create a type Dog with a method Speak that returns ‘Woof’.
Notice — we never explicitly say ‘Dog implements Speaker’. [pause] But because Dog has the Speak method, it automatically does!
In main, we assign a Dog to a Speaker variable, and when we call s.Speak(), the output is ‘Woof’.”

Why It’s Useful (1:20–2:10)
“This matters because interfaces let you write flexible code. [pause] For example, you can have multiple types — Dog, Cat, Human — each implementing Speak. Any function that accepts a Speaker can work with all of them. [pause] This is huge in real-world Go projects, especially for testing, mocking, and designing scalable systems. [pause] You get polymorphism without complicated inheritance trees.”

Outro (2:10–2:30)
“So, do you like Go’s automatic interface implementation, or do you prefer explicit declarations like in Java? [pause] Comment your thoughts below, and don’t forget to subscribe for more Go tutorials made simple.”